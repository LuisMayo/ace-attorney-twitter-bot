import sys

sys.path.append('./objection_engine')
sys.path.append('./video-splitter')
import time
import os
from persistqueue import Queue
import threading
import random
import settings
from comment_list_brige import Comment
from objection_engine.renderer import render_comment_list
from mastodon import Mastodon

splitter = __import__("ffmpeg-split")

mention_queue = Queue('queue')
delete_queue = Queue('delete')


def update_id(id):
    with open('done_ids.txt', 'a') as idFile:
        idFile.write(str(id)+"\n")


def check_mentions():
    global done_ids
    global mention_queue
    while True:
        try:
            mentions = mastodon.notifications(limit=30, mentions_only=True)
            if len(mentions) > 0:
                for mention in mentions:
                    last_id = mention["id"]
                    status_id = mention["status"]["id"]
                    status_dict = mastodon.status(status_id)
                    if 'render' in status_dict["content"] and last_id not in done_ids:
                        mention_queue.put(status_dict)
                        print(mention_queue.qsize())
                    # if 'delete' in tweet.full_text:
                    #    delete_queue.put(tweet)
                update_id(last_id)
        except Exception as e:
            print(e)
        time.sleep(20)


def process_deletions():
    global delete_queue


def process_tweets():
    global mention_queue
    while True:
        thread = []
        try:
            status = mention_queue.get()
            # print(mastodon.status_context(status["id"])["ancestors"])
            thread_dicts = mastodon.status_context(status["id"])["ancestors"][::-1]
            songs = ['PWR', 'JFA', 'TAT', 'rnd']

            if 'music=' in status["content"]:
                music_stat = status["content"].split('music=', 1)[1][:3]
            else:
                music_stat = 'PWR'

            if music_stat == 'rnd':
                music_stat = random.choices(songs, [1, 1, 1, 0], k=1)[0]

            if music_stat not in songs:  # If the music is written badly in the mention tweet, the bot will remind how to write it properly
                try:
                    mastodon.status_reply(status, 'BROKEN. Dont select music! The music argument format is incorrect. The possibilities '
                                                  'are: \nPWR: Phoenix Wright Ace Attorney \nJFA: '
                                                  'Justice for '
                                                  'All \nTAT: Trials and Tribulations \nrnd: Random')
                except Exception as musicerror:
                    print(musicerror)
            else:
                for post in thread_dicts:
                    current_status = post
                    thread.insert(0, Comment(current_status).to_message())

                if len(thread) >= 1:
                    output_filename = str(status["id"]) + '.mp4'
                    render_comment_list(thread, music_code=music_stat, output_filename=output_filename)
                    files = splitter.split_by_seconds(output_filename, 140, vcodec='libx264')

                    try:
                        # media = mastodon.media_post(output_filename)
                        # mastodon.status_reply(status, "Here's the court session", media_ids=media)
                        for file_name in files:
                            #    print("trying media")
                            media = mastodon.media_post(file_name)
                            #    print("trying status")
                            mastodon.status_reply(status, "Here's the court session", media_ids=media)
                        #    mastodon.status_post("Here's the court session", in_reply_to_id=status["id"], media_ids=media)
                        #    print("tried status")
                    except Exception as e:
                        print(e)
                        print("Can't post")
                        mention_queue.put(status)
                        time.sleep(600)
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

    # Load done IDs
    try:
        with open('done_ids.txt', 'r') as idFile:
            done_ids = set(idFile.readlines())
    except FileNotFoundError:
        done_ids = None

    # Init

    producer = threading.Thread(target=check_mentions)
    consumer = threading.Thread(target=process_tweets)
    threading.Thread(target=process_tweets).start()
    producer.start()
    consumer.start()
