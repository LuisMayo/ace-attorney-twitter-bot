import sys

sys.path.append('./objection_engine')
sys.path.append('./video-splitter')
from collections import Counter
import re
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
    with open('id.txt', 'w') as idFile:
        idFile.write(id)


def postVideoTweet(reply_id, filename):
    uploaded_media = api.media_upload(filename, media_category='TWEET_VIDEO')
    while uploaded_media.processing_info['state'] == 'pending':
        time.sleep(uploaded_media.processing_info['check_after_secs'])
        uploaded_media = api.get_media_upload_status(uploaded_media.media_id_string)
    time.sleep(10)
    return api.update_status('Your video is ready. Do you want it removed? contact @/LuisMayoV',
                             in_reply_to_status_id=reply_id, auto_populate_reply_metadata=True,
                             media_ids=[uploaded_media.media_id_string])


def check_mentions():
    global lastId
    global mention_queue
    while True:
        try:
            if lastId is None:
                mentions = mastodon.notifications(mentions_only=True)
            else:
                mentions = mastodon.notifications(since_id=lastId, mentions_only=True)
            if len(mentions) > 0:
                for mention in mentions:
                    lastId = mention["id"]
                    status_id = mention["status"]["id"]
                    status_dict = mastodon.status(status_id)
                    #print("Id: " + str(status_id) + " content: " + status_dict["content"])
                    if 'render' in status_dict["content"]:
                        mention_queue.put(status_dict.deepcopy())
                        print(mention_queue.qsize())
                    #if 'delete' in tweet.full_text:
                    #    delete_queue.put(tweet)
                update_id(str(lastId))
        except Exception as e:
            print(e)
        time.sleep(20)


def process_deletions():
    global delete_queue


def process_tweets():
    global mention_queue
    while True:
        try:
            status = mention_queue.get()
            thread_dicts = mastodon.status_context["ancestors"].reverse()
            thread = []
            current_status = status
            songs = ['PWR', 'JFA', 'TAT', 'rnd']

            if 'music=' in status["content"]:
                music_stat = status["content"].split('music=', 1)[1][:3]
            else:
                music_stat = 'PWR'

            if music_stat == 'rnd':
                music_stat = random.choices(songs, [1, 1, 1, 0], k=1)[0]

            if music_stat not in songs:  # If the music is written badly in the mention tweet, the bot will remind how to write it properly
                try:
                    mastodon.status_post(
                        '@' + status["account"]["acct"] + ' The music argument format is incorrect. The posibilities are: \nPWR: Phoenix Wright Ace Attorney \nJFA: Justice for All \nTAT: Trials and Tribulations \nrnd: Random',
                        in_reply_to_status_id=status["id"])
                except Exception as musicerror:
                    print(musicerror)
            else:
                while len(thread_dicts) > 0:
                    for post in thread_dicts:
                        current_status = post.deepcopy()
                        thread.insert(0, Comment(current_status).to_message())
                        thread_dicts.pop(0)

                if len(thread) >= 1:
                    output_filename = tweet.id_str + '.mp4'
                    render_comment_list(thread, music_code=music_stat, output_filename=output_filename)
                    files = splitter.split_by_seconds(output_filename, 140, vcodec='libx264')
                    reply_to_tweet = status
                    try:
                        for file_name in files:
                            reply_to_tweet = postVideoTweet(reply_to_tweet.id_str, file_name)
                    except tweepy.error.TweepError as e:
                        limit = False
                        try:
                            print(e.api_code)
                            if e.api_code == 185:
                                print("I'm Rated-limited :(")
                                limit = True
                                mention_queue.put(tweet)
                                time.sleep(900)
                        except Exception as parsexc:
                            print(parsexc)
                        try:
                            if not limit:
                                api.update_status('@' + tweet.author.screen_name + ' ' + str(e),
                                                  in_reply_to_status_id=tweet.id_str)
                        except Exception as second_error:
                            print(second_error)
                        print(e)
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

    # Load last ID
    try:
        with open('id.txt', 'r') as idFile:
            lastId = idFile.read()
    except FileNotFoundError:
        lastId = None

    # Init
    print("init")

    producer = threading.Thread(target=check_mentions)
    consumer = threading.Thread(target=process_tweets)
    threading.Thread(target=process_tweets).start()
    producer.start()
    consumer.start()
