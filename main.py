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
# TODO: cache and database
# from cacheout import LRUCache
# from pymongo import MongoClient
from mastodon import Mastodon, MastodonError, MastodonRatelimitError, CallbackStreamListener

splitter = __import__("ffmpeg-split")

mention_queue = Queue('queue')
delete_queue = Queue('delete')
available_songs = get_all_music_available()
# TODO: cache and database
# cache = LRUCache()
# mongo_client = MongoClient('mongodb://localhost/')
# collection = mongo_client['aa_tw_bot']['sent_videos']

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
    mastodon.status_reply(status, 'Your video is ready. Do you want it removed? Reply to me saying "remove" or "delete"', media_ids=media)

def check_mention(mention):
    global mention_queue
    global render_regex

    status_dict = mention["status"]
    if re.search(render_regex, status_dict["content"]) is not None:
        mention_queue.put(status_dict)
        print(f"Queue size: {mention_queue.qsize()}")
    # TODO: Implement deletion for Mastodon
    # if ('delete' in status_dict["content"].lower() or 'remove' in status_dict["content"].lower()) and tweet.in_reply_to_user_id == me_response.id:
    #     delete_queue.put(status_dict)

def check_mentions():
    # Load last ID
    try:
        with open('id.txt', 'r') as idFile:
            lastId = idFile.read()
    except FileNotFoundError:
        lastId = None

    def get_existing_mentions():
        nonlocal lastId
        # mastodon.notifications has mention_only parameter but it doesn't do anything
        # https://github.com/halcy/Mastodon.py/issues/206#issuecomment-666271454
        while True:
            mentions = [n for n in mastodon.notifications(since_id=lastId) if n["type"] == "mention"]
            for mention in mentions:
                lastId = mention["id"]
                check_mention(mention)
            if len(mentions) == 0:
                break
            update_id(str(lastId))

    def notification_handler(notification):
        nonlocal lastId
        if notification["type"] == "mention":
            print("n")
            lastId = notification["id"]
            check_mention(notification)
            update_id(str(lastId))

    while True:
        try:
            get_existing_mentions()
            mastodon.stream_user(CallbackStreamListener(notification_handler=notification_handler))
        except MastodonError as e:
            print(e)
        time.sleep(20)


def process_deletions():
    global delete_queue
    # TODO: Implement deletion for Mastodon
    # while True:
    #     try:
    #         tweet = delete_queue.get()
    #         tweet_to_remove = api.get_status(tweet.in_reply_to_status_id_str, tweet_mode="extended")
    #         if tweet_to_remove.user.id_str != me or not hasattr(tweet_to_remove, 'extended_entities') or 'media' not in tweet_to_remove.extended_entities or len(tweet_to_remove.extended_entities['media']) == 0:
    #             # If they don't ask us to remove a video just ignore them
    #             continue
    #         filter = {"tweets": tweet.in_reply_to_status_id_str}
    #         doc = collection.find_one(filter)
    #     except Exception as e:
    #         print(e)
    #         continue
    #     if doc is None:
    #         try:
    #             api.update_status('I can\'t delete the video, contact @/LuisMayoV', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
    #         except:
    #             pass
    #     elif tweet.user.id_str not in doc['users']:
    #         try:
    #             api.update_status('You are not authorized to remove this video', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
    #         except:
    #             pass
    #     else:
    #         try:
    #             for video in doc['tweets']:
    #                 api.destroy_status(video)
    #         except Exception as e:
    #             try:
    #                 print('Error while removing')
    #                 print(e)
    #                 api.update_status('I can\'t delete the video, contact @/LuisMayoV', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
    #             except:
    #                 pass
    #         try:
    #             collection.delete_one({'_id' : doc['_id']})
    #         except Exception as e:
    #             print(e)
    #         try:
    #             api.create_favorite(tweet.id_str)
    #         except:
    #             pass
    #     time.sleep(1)



def process_tweets():
    global mention_queue
    global update_queue_params
    global me
    while True:
        thread = []
        try:
            status = mention_queue.get()
            update_queue_params['last_time'] = status["created_at"]
            # TODO: activate cache thing
            # current_tweet = tweet
            # previous_tweet = None
            # # The cache key is the key for the cache, it consists on the tweet ID and the selected music
            # cache_key = None
            thread_dicts = mastodon.status_context(status["id"])["ancestors"][::-1]
            # TODO: enable database logging
            # # These variables are stored in mongodb database
            # users_in_video = [tweet.user.id_str]
            # video_ids = []

            if 'music=' in status["content"]:
                music_stat = status["content"].split('music=', 1)[1][:3]
            else:
                music_stat = 'PWR'

            # TODO: activate cache thing
            # if current_tweet is not None and (current_tweet.in_reply_to_status_id_str or hasattr(current_tweet, 'quoted_status_id_str')):
            #     cache_key = (current_tweet.in_reply_to_status_id_str or current_tweet.quoted_status_id_str) + '/' + music_tweet.lower()

            # cached_value = cache.get(cache_key)

            if not is_music_available(music_stat):  # If the music is written badly in the mention tweet, the bot will remind how to write it properly
                try:
                    mastodon.status_reply(status, 'The music argument format is incorrect. The posibilities are: \n' + '\n'.join(available_songs))
                except Exception as musicerror:
                    print(musicerror)
            # TODO: activate cache thing
            # elif cached_value is not None:
            #     api.update_status('I\'ve already done that, here you have ' + cached_value, in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
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
                        postVideoTweet(status, output_filename)
                    except MastodonRatelimitError as e:
                        print("I'm Rated-limited :(")
                        mention_queue.put(status)
                        time.sleep(900)
                        print(e)
                    except MastodonError as e:
                        try:
                            mastodon.status_reply(status, str(e))
                        except Exception as second_error:
                            print(second_error)
                        print(e)
                    # TODO: enable database logging
                    # # We insert the object into the database
                    # collection.insert_one({
                    #     'users': users_in_video,
                    #     'tweets': video_ids,
                    #     'time': int(time.time())
                    # })
                    clean(thread, output_filename, files)
            time.sleep(1)
        except Exception as e:
            clean(thread, None, [])
            print(e)


def clean(thread, output_filename, files):
    global mention_queue
    # We mark the task as done so it deletes the element from the queue on disk
    mention_queue.task_done()
    try:
        for comment in thread:
            if hasattr(comment, 'evidence') and comment.evidence is not None:
                os.remove(comment.evidence)
    except Exception as second_e:
        print(second_e)
    try:
        for file_name in files:
            os.remove(file_name)
    except Exception as second_e:
        print(second_e)
    try:
        if output_filename is not None:
            os.remove(output_filename)
    except Exception as second_e:
        print(second_e)


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
    # TODO: Mastodon API
    # me_response = api.me()
    # # render_regex = f'^ *@{me_response.screen_name} render'
    render_regex = 'render'
    # me = me_response.id_str
    update_queue_params = {
        'queue': mention_queue,
        'last_time': None,
        'mastodon': mastodon
    }
    producer = threading.Thread(target=check_mentions)
    consumer = threading.Thread(target=process_tweets)
    threading.Thread(target=process_tweets).start()
    # threading.Thread(target=update_queue_length, args=[update_queue_params]).start()
    threading.Thread(target=process_deletions).start()
    producer.start()
    consumer.start()
