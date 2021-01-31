import sys
import json
sys.path.insert(0, './ace-attorney-reddit-bot')
from collections import Counter 
import tweepy
import re
import sched, time
import os

import anim
from comment_list_brige import Comment


def sanitize_tweet(tweet):
    return
    # tweet.text = re.sub(r'^(@\S+) +', '', tweet)
    # tweet.text = re.sub(r'(https)\S*', '', tweet)

def update_id(id):
    with open('id.txt', 'w') as idFile:
        idFile.write(id)

def check_mentions():
    global lastId
    mentions = api.mentions_timeline(count='200') if lastId == None else api.mentions_timeline(since_id=lastId, count='200')
    for tweet in mentions:
        lastId = tweet.id_str
        if 'render' in tweet.text:
            thread = []
            users_to_names = {} # This will serve to link @display_names with usernames
            counter = Counter()
            current_tweet = tweet
            # In the case of Quotes I have to check for its presence instead of whether its None because Twitter API designers felt creative that week
            while current_tweet.in_reply_to_status_id_str or hasattr(current_tweet, 'quoted_status_id_str'):
                current_tweet = api.get_status(current_tweet.in_reply_to_status_id_str or current_tweet.quoted_status_id_str)
                sanitize_tweet(current_tweet)
                users_to_names[current_tweet.author.screen_name] = current_tweet.author.name
                counter.update({current_tweet.author.screen_name: 1})  
                thread.insert(0, Comment(current_tweet))
            most_common = [users_to_names[t[0]] for t in counter.most_common()]
            characters = anim.get_characters(most_common)
            output_filename = tweet.id_str + '.mp4'
            anim.comments_to_scene(thread, characters, output_filename=output_filename)
            try:
                uploaded_media = api.media_upload(output_filename, media_category='TWEET_VIDEO')
                while (uploaded_media.processing_info['state'] == 'pending'):
                    time.sleep(uploaded_media.processing_info['check_after_secs'])
                    uploaded_media = api.get_media_upload_status(uploaded_media.media_id_string)
                api.update_status('@' + tweet.author.screen_name + ' ', in_reply_to_status_id=tweet.id_str, media_ids=[uploaded_media.media_id_string])
            except tweepy.error.TweepError as e:
                try:
                    api.update_status('@' + tweet.author.screen_name + ' ' + e, in_reply_to_status_id=tweet.id_str)
                except:
                    print(e)
                print(e)
            os.remove(output_filename)
            update_id(tweet.id_str)
        else:
            update_id(tweet.id_str)
    s.enter(20, 2, check_mentions)

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

s = sched.scheduler(time.time, time.sleep)
s.enter(0, 2, check_mentions)
s.run()
