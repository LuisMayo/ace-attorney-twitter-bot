import sys
import json
sys.path.insert(0, './ace-attorney-reddit-bot')
from collections import Counter 
import tweepy
import re
import time
import os
import queue
import threading

import anim
from comment_list_brige import Comment

mention_queue = queue.Queue()


def sanitize_tweet(tweet):
    tweet.full_text = re.sub(r'^(@\S+ )+', '', tweet.full_text)
    tweet.full_text = re.sub(r'(https)\S*', '(link)', tweet.full_text)

def update_id(id):
    with open('id.txt', 'w') as idFile:
        idFile.write(id)

def check_mentions():
    global lastId
    global mention_queue
    while True:
        try:
            mentions = api.mentions_timeline(count='200', tweet_mode="extended") if lastId == None else api.mentions_timeline(since_id=lastId, count='200', tweet_mode="extended")
            if len(mentions) > 0:
                lastId = mentions[0].id_str
                for tweet in mentions[::-1]:
                    if 'render' in tweet.full_text:
                        mention_queue.put(tweet)
                        print(mention_queue.qsize())
        except Exception as e:
            print(e)
        time.sleep(20)

def process_tweets():
    global mention_queue
    while True:
        try:
            tweet = mention_queue.get()
            update_id(tweet.id_str)
            thread = []
            users_to_names = {} # This will serve to link @display_names with usernames
            counter = Counter()
            current_tweet = tweet
            # In the case of Quotes I have to check for its presence instead of whether its None because Twitter API designers felt creative that week
            while (current_tweet is not None) and (current_tweet.in_reply_to_status_id_str or hasattr(current_tweet, 'quoted_status_id_str')):
                try:
                    current_tweet = api.get_status(current_tweet.in_reply_to_status_id_str or current_tweet.quoted_status_id_str, tweet_mode="extended")
                    sanitize_tweet(current_tweet)
                    users_to_names[current_tweet.author.screen_name] = current_tweet.author.name
                    counter.update({current_tweet.author.screen_name: 1})  
                    thread.insert(0, Comment(current_tweet))
                except tweepy.error.TweepError as e:
                    try:
                        api.update_status('@' + tweet.author.screen_name + ' I\'m sorry. I wasn\'t able to retrieve the full thread. Deleted tweets or private accounts may exist', in_reply_to_status_id=tweet.id_str)
                    except Exception as second_error:
                        print (second_error)
                    current_tweet = None
            if (len(users_to_names) >= 2):
                most_common = [users_to_names[t[0]] for t in counter.most_common()]
                characters = anim.get_characters(most_common)
                output_filename = tweet.id_str + '.mp4'
                anim.comments_to_scene(thread, characters, output_filename=output_filename)
                # Give some time to the other thread
                time.sleep(1)
                try:
                    uploaded_media = api.media_upload(output_filename, media_category='TWEET_VIDEO')
                    while (uploaded_media.processing_info['state'] == 'pending'):
                        time.sleep(uploaded_media.processing_info['check_after_secs'])
                        uploaded_media = api.get_media_upload_status(uploaded_media.media_id_string)
                    api.update_status('@' + tweet.author.screen_name + ' ', in_reply_to_status_id=tweet.id_str, media_ids=[uploaded_media.media_id_string])
                except tweepy.error.TweepError as e:
                    limit = False
                    try:
                        print(e.api_code)
                        if (e.api_code == 324):
                            print("I'm Rated-limited :(")
                            limit = True
                            mention_queue.put(tweet)
                            time.sleep(900)
                    except Exception as parsexc:
                        print(parsexc)
                    try:
                        if not limit:
                            api.update_status('@' + tweet.author.screen_name + ' ' + str(e), in_reply_to_status_id=tweet.id_str)
                    except Exception as second_error:
                        print (second_error)
                    print(e)
                os.remove(output_filename)
            else:
                try:
                    api.update_status('@' + tweet.author.screen_name + " There should be at least two people in the conversation", in_reply_to_status_id=tweet.id_str)
                except Exception as e:
                    print(e)
            time.sleep(1)
        except Exception as e:
            print(e)


################################## Main

# Load keys
with open('keys.json', 'r') as keyfile:
    keys = json.load(keyfile)

# Load last ID
try:
    with open('id.txt', 'r') as idFile:
        lastId = idFile.read()
except FileNotFoundError:
    lastId = None

# Init
auth = tweepy.OAuthHandler(keys['consumerApiKey'], keys['consumerApiSecret'])
auth.set_access_token(keys['accessToken'], keys['accessTokenSecret'])
api = tweepy.API(auth)
producer = threading.Thread(target=check_mentions)
consumer = threading.Thread(target=process_tweets)
producer.start()
consumer.start()
