from datetime import datetime, timezone
import sys
from update_queue_lenght import update_queue_length
sys.path.append('./objection_engine')
sys.path.append('./video-splitter')
import re
import time
import os
from persistqueue import Queue
import threading
import time
import settings
from comment_list_brige import Comment
from objection_engine import render_comment_list, is_music_available, get_all_music_available
from cacheout import LRUCache
from mongita import MongitaClientDisk
from mastodon import Mastodon, MastodonError, MastodonRatelimitError, StreamListener

splitter = __import__("ffmpeg-split")

mention_queue = Queue('queue')
delete_queue = Queue('delete')
available_songs = get_all_music_available()
cache = LRUCache()
mongo_client = MongitaClientDisk()
collection = mongo_client['aa_tw_bot']['sent_videos']

def filter_beginning_mentions(match):
    mentions = match[0].strip().split(' ')
    index = next((index for index,x in enumerate(mentions) if x in mentions[:index]), len(mentions))
    message = ' '.join(mentions[index:])
    return message + ' ' if len(message) > 0 else message

def update_id(id):
    with open('id.txt', 'w') as idFile:
        idFile.write(id)

def postVideoTweet(status, filename):
    media = mastodon.media_post(filename)
    time.sleep(10)
    return mastodon.status_reply(status, 'Your video is ready. Do you want it removed? Reply to me saying "remove" or "delete"', media_ids=media)

def check_mention(mention):
    global mention_queue
    global render_regex

    status_dict = mention["status"]
    if re.search(render_regex, status_dict["content"]) is not None:
        mention_queue.put(status_dict)
        print(f"Queue size: {mention_queue.qsize()}")
    if ('delete' in status_dict["content"].lower() or 'remove' in status_dict["content"].lower()) and status_dict["in_reply_to_account_id"] == me_response["id"]:
        delete_queue.put(status_dict)

def check_mentions():
    def get_existing_mentions(lastId):
        # mastodon.notifications has mention_only parameter but it doesn't do anything
        # https://github.com/halcy/Mastodon.py/issues/206#issuecomment-666271454
        while True:
            mentions = [n for n in mastodon.notifications(since_id=lastId) if n["type"] == "mention"]
            for mention in mentions:
                lastId = mention["id"]
                print(f'Mention id from REST: {lastId}')
                check_mention(mention)
            if len(mentions) == 0:
                break
            update_id(str(lastId))

    class Listener(StreamListener):
        def __init__(self) -> None:
            super().__init__()
            try:
                with open('id.txt', 'r') as idFile:
                    self.lastId = int(idFile.read())
            except FileNotFoundError:
                self.lastId = None

        def on_notification(self, notification):
            if notification["type"] != "mention":
                return
            if notification["id"] <= self.lastId:
                print(f'Got duplicated mention id {notification["id"]}, skipping')
                return
            self.lastId = notification["id"]
            print(f'Mention id from stream: {self.lastId}')
            check_mention(notification)
            update_id(str(self.lastId))

        def handle_stream(self, response):
            get_existing_mentions(self.lastId)
            return super().handle_stream(response)

    while True:
        try:
            mastodon.stream_user(Listener())
        except MastodonError as e:
            print(f'Error from stream: {e}')
        time.sleep(20)


def process_deletions():
    global delete_queue
    while True:
        try:
            status = delete_queue.get()
            status_to_remove = mastodon.status(status["in_reply_to_id"])
            if status_to_remove["account"]["id"] != me or len(status_to_remove.media_attachments) == 0:
                # If they don't ask us to remove a video just ignore them
                continue
            filter = {"statuses": status["in_reply_to_id"]}
            doc = collection.find_one(filter)
        except Exception as e:
            print(f'Error when checking deletion: {e}')
            continue
        if doc is None:
            try:
                mastodon.status_reply(status, f'I can\'t delete the video, contact @/{settings.ADMIN}')
            except:
                pass
        elif status["account"]["id"] not in doc['users']:
            try:
                mastodon.status_reply(status, 'You are not authorized to remove this video')
            except:
                pass
        else:
            try:
                for video in doc['statuses']:
                    mastodon.status_delete(video)
            except Exception as e:
                try:
                    print('Error while removing')
                    print(e)
                    mastodon.status_reply(status, f'I can\'t delete the video, contact @/{settings.ADMIN}')
                except:
                    pass
            try:
                collection.delete_one({'_id' : doc['_id']})
            except Exception as e:
                print(e)
            try:
                mastodon.status_favourite(status)
            except:
                pass
        time.sleep(1)



def process_tweets():
    global mention_queue
    global update_queue_params
    global me
    while True:
        thread = []
        try:
            status = mention_queue.get()
            update_queue_params['last_time'] = status["created_at"]
            # The cache key is the key for the cache, it consists on the status ID and the selected music
            cache_key = None
            thread_dicts = mastodon.status_context(status["id"])["ancestors"][::-1]
            # These variables are stored in mongodb database
            users_in_video = [status["account"]["id"]]
            video_ids = []

            if 'music=' in status["content"]:
                music_stat = status["content"].split('music=', 1)[1][:3]
            else:
                music_stat = 'PWR'

            if status is not None and status["in_reply_to_id"]:
                cache_key = f"{status['in_reply_to_id']}/{music_stat.lower()}"

            cached_value = cache.get(cache_key)

            if not is_music_available(music_stat):  # If the music is written badly in the mention tweet, the bot will remind how to write it properly
                try:
                    mastodon.status_reply(status, 'The music argument format is incorrect. The posibilities are: \n' + '\n'.join(available_songs))
                except Exception as musicerror:
                    print(f'Error when replying music error: {musicerror}')
            elif cached_value is not None:
                mastodon.status_reply(status, 'I\'ve already done that, here you have ' + cached_value)
                clean(thread, None, [])
            else:
                for post in thread_dicts:
                    current_status = post
                    print("adding status "+str(current_status["id"])+" to thread")
                    thread.insert(0, Comment(current_status).to_message())

                if len(thread) >= 1:
                    output_filename = str(status["id"]) + '.mp4'
                    print("trying to render")
                    render_comment_list(thread, music_code=music_stat, output_filename=output_filename, resolution_scale=2)
                    files = []

                    try:
                        reply_to_tweet = postVideoTweet(status, output_filename)
                        video_ids.append(reply_to_tweet["id"])
                        cached_value = f'{settings.INSTANCE_URL}/@{me_response["username"]}/{reply_to_tweet["id"]}'
                        cache.add(cache_key, cached_value)
                    except MastodonRatelimitError as e:
                        print("I'm Rated-limited :(")
                        mention_queue.put(status)
                        time.sleep(900)
                        print(e)
                    except MastodonError as e:
                        try:
                            mastodon.status_reply(status, str(e))
                        except Exception as second_error:
                            print(f'Second error: {second_error}')
                        print(f'Error while posting video: {e}')
                    # We insert the object into the database
                    collection.insert_one({
                        'users': users_in_video,
                        'statuses': video_ids,
                        'time': int(time.time())
                    })
                    clean(thread, output_filename, files)
            time.sleep(1)
        except Exception as e:
            clean(thread, None, [])
            print(f'Error while processing thread: {e}')


def clean(thread, output_filename, files):
    global mention_queue
    # We mark the task as done so it deletes the element from the queue on disk
    mention_queue.task_done()
    try:
        for comment in thread:
            if hasattr(comment, 'evidence') and comment.evidence is not None:
                os.remove(comment.evidence)
    except Exception as second_e:
        print(f'Error while cleanup: {second_e}')
    try:
        for file_name in files:
            os.remove(file_name)
    except Exception as second_e:
        print(f'Error while cleanup: {second_e}')
    try:
        if output_filename is not None:
            os.remove(output_filename)
    except Exception as second_e:
        print(f'Error while cleanup: {second_e}')


if __name__ == "__main__":
    if not os.path.exists('clientcred.secret'):
        Mastodon.create_app(
            'AceBot',
            api_base_url=settings.INSTANCE_URL,
            to_file='clientcred.secret'
        )
    if not os.path.exists('usercred.secret'):
        mastodon = Mastodon(
            client_id='clientcred.secret',
            api_base_url=settings.INSTANCE_URL
        )
        mastodon.log_in(
            settings.LOGIN,
            settings.PASSWORD,
            to_file='usercred.secret'
        )
    else:
        mastodon = Mastodon(
            access_token='usercred.secret',
            api_base_url=settings.INSTANCE_URL
        )

    # Init
    me_response = mastodon.account_verify_credentials()
    # # render_regex = f'^ *@{me_response.screen_name} render'
    render_regex = 'render'
    me = me_response["id"]
    update_queue_params = {
        'queue': mention_queue,
        'last_time': None,
        'mastodon': mastodon
    }
    producer = threading.Thread(target=check_mentions)
    consumer = threading.Thread(target=process_tweets)
    threading.Thread(target=process_tweets).start()
    threading.Thread(target=update_queue_length, args=[update_queue_params]).start()
    threading.Thread(target=process_deletions).start()
    producer.start()
    consumer.start()
