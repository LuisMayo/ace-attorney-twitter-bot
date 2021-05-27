import sys
import json

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
                mentions = mastodon.notifications(limit='100', mentions_only=True)
            else:
                mentions = mastodon.notifications(since_id=lastId, limit='100', mentions_only=True)
            if len(mentions) > 0:
                for status in mentions:
                    lastId = status["id"]
                    status_dict = mastodon.status(lastId)
                    if 'render' in status_dict["content"]:
                        mention_queue.put(status_dict.copy())
                        print("Id: " + status["id"] + "content: " + status_dict["content"])
                        print(mention_queue.qsize())
                    #if 'delete' in tweet.full_text:
                    #    delete_queue.put(tweet)
                update_id(lastId)
        except Exception as e:
            print(e)
        time.sleep(20)


def process_deletions():
    global delete_queue


def process_tweets():
    global mention_queue
    while True:
        try:
            tweet = mention_queue.get()
            thread = []
            current_tweet = tweet
            songs = ['PWR', 'JFA', 'TAT', 'rnd']

            if 'music=' in tweet.full_text:
                music_tweet = tweet.full_text.split('music=', 1)[1][:3]
            else:
                music_tweet = 'PWR'

            if music_tweet == 'rnd':
                music_tweet = random.choices(songs, [1, 1, 1, 0], k=1)[0]

            if music_tweet not in songs:  # If the music is written badly in the mention tweet, the bot will remind how to write it properly
                try:
                    api.update_status(
                        '@' + tweet.author.screen_name + ' The music argument format is incorrect. The posibilities are: \nPWR: Phoenix Wright Ace Attorney \nJFA: Justice for All \nTAT: Trials and Tribulations \nrnd: Random',
                        in_reply_to_status_id=tweet.id_str)
                except Exception as musicerror:
                    print(musicerror)
            else:
                # In the case of Quotes I have to check for its presence instead of whether its None because Twitter API designers felt creative that week
                i = 0
                # If we have 2 hate detections we stop rendering the video all together
                hate_detections = 0
                while (current_tweet is not None) and (
                        current_tweet.in_reply_to_status_id_str or hasattr(current_tweet, 'quoted_status_id_str')):
                    try:
                        current_tweet = api.get_status(
                            current_tweet.in_reply_to_status_id_str or current_tweet.quoted_status_id_str,
                            tweet_mode="extended")
                        thread.insert(0, Comment(current_tweet).to_message())
                        i += 1
                        if (current_tweet is not None and i >= settings.MAX_TWEETS_PER_THREAD):
                            current_tweet = None
                            api.update_status(
                                '@' + tweet.author.screen_name + f' Sorry, the thread was too long, I\'ve only retrieved {i} tweets',
                                in_reply_to_status_id=tweet.id_str)
                    except tweepy.error.TweepError as e:
                        try:
                            api.update_status(
                                '@' + tweet.author.screen_name + ' I\'m sorry. I wasn\'t able to retrieve the full thread. Deleted tweets or private accounts may exist',
                                in_reply_to_status_id=tweet.id_str)
                        except Exception as second_error:
                            print(second_error)
                        current_tweet = None
                if (len(thread) >= 1):
                    output_filename = tweet.id_str + '.mp4'
                    render_comment_list(thread, music_code=music_tweet, output_filename=output_filename)
                    files = splitter.split_by_seconds(output_filename, 140, vcodec='libx264')
                    reply_to_tweet = tweet
                    try:
                        for file_name in files:
                            reply_to_tweet = postVideoTweet(reply_to_tweet.id_str, file_name)
                    except tweepy.error.TweepError as e:
                        limit = False
                        try:
                            print(e.api_code)
                            if (e.api_code == 185):
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
    producer = threading.Thread(target=check_mentions)
    consumer = threading.Thread(target=process_tweets)
    threading.Thread(target=process_tweets).start()
    producer.start()
    #consumer.start()
