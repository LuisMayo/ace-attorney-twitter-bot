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
import random

import anim
from comment_list_brige import Comment
from datetime import datetime

mention_queue = queue.Queue()

def init_twitter_api():
    global api
    global main_api # This is used to retrieve the notifications
    global next_account
    auth = tweepy.OAuthHandler(keys[next_account]['consumerApiKey'], keys[next_account]['consumerApiSecret'])
    auth.set_access_token(keys[next_account]['accessToken'], keys[next_account]['accessTokenSecret'])
    api = tweepy.API(auth)
    if ('main_api' not in globals() or main_api is None):
        auth = tweepy.OAuthHandler(keys[0]['consumerApiKey'], keys[0]['consumerApiSecret'])
        auth.set_access_token(keys[0]['accessToken'], keys[0]['accessTokenSecret'])
        main_api = tweepy.API(auth)
    next_account += 1
    next_account = next_account % len(keys)

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
            mentions = main_api.mentions_timeline(count='200', tweet_mode="extended") if lastId == None else main_api.mentions_timeline(since_id=lastId, count='200', tweet_mode="extended")
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
    global lastTime
    while True:
        try:
            tweet = mention_queue.get()
            update_id(tweet.id_str)
            thread = []
            users_to_names = {} # This will serve to link @display_names with usernames
            counter = Counter()
            current_tweet = tweet
            songs = ['PWR', 'JFA', 'TAT', 'rnd']
            
            if 'music=' in tweet.full_text:
                music_tweet = tweet.full_text.split('music=', 1)[1][:3]
            else:
                music_tweet = 'PWR'
                
            if music_tweet == 'rnd':
                music_tweet = random.choices(songs, [1, 1, 1, 0], k=1)[0]
            
            if music_tweet not in songs: # If the music is written badly in the mention tweet, the bot will remind how to write it properly
                try:
                    api.update_status('@' + tweet.author.screen_name + ' The music argument format is incorrect. The posibilities are: \nPWR: Phoenix Wright Ace Attorney \nJFA: Justice for All \nTAT: Trials and Tribulations \nrnd: Random', in_reply_to_status_id=tweet.id_str)
                except Exception as musicerror:
                    print(musicerror)
            else:
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
                    anim.comments_to_scene(thread, characters, name_music = music_tweet, output_filename=output_filename)
                    try:
                        uploaded_media = api.media_upload(output_filename, media_category='TWEET_VIDEO')
                        while (uploaded_media.processing_info['state'] == 'pending'):
                            time.sleep(uploaded_media.processing_info['check_after_secs'])
                            uploaded_media = api.get_media_upload_status(uploaded_media.media_id_string)
                        # Twitter may not have properly proccesed the video even if it says so
                        time.sleep(2)
                        api.update_status('@' + tweet.author.screen_name + ' ', in_reply_to_status_id=tweet.id_str, media_ids=[uploaded_media.media_id_string])
                    except tweepy.error.TweepError as e:
                        limit = False
                        try:
                            print(e.api_code)
                            if (e.api_code == 185):
                                print("I'm Rated-limited :(")
                                limit = True
                                mention_queue.put(tweet)
                                current_date = datetime.now(tz=None)
                                if ('lastTime' in globals() and lastTime is not None and (current_date - lastTime).seconds < 300 ):
                                    time.sleep(900)
                                    print("I'm double rate limited")
                                else:
                                    init_twitter_api()
                                lastTime = datetime.now(tz=None)
                        except Exception as parsexc:
                            print(parsexc)
                        try:
                            if not limit:
                                api.update_status('@' + tweet.author.screen_name + ' ' + str(e), in_reply_to_status_id=tweet.id_str)
                        except Exception as second_error:
                            print(second_error)
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
    
def restore_account():
    global mention_queue
    global next_account
    while True:
        mention_queue.join()
        next_account = 0
        init_twitter_api()
        time.sleep(10)


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
next_account = 0
init_twitter_api()
producer = threading.Thread(target=check_mentions)
consumer = threading.Thread(target=process_tweets)
threading.Thread(target=restore_account).start()
producer.start()
consumer.start()
