import sys
import json
sys.path.insert(0, './ace-attorney-reddit-bot')
from collections import Counter 
import tweepy
import re
# import sched, time

import anim
from comment_list_brige import Comment


def sanitize_tweet(tweet):
    return
    # tweet.text = re.sub(r'^(@\S+) +', '', tweet)
    # tweet.text = re.sub(r'(https)\S*', '', tweet)



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

# s = sched.scheduler(time.time, time.sleep)


mentions = api.mentions_timeline(count='200') if lastId == None else api.mentions_timeline(since_id=lastId, count='200')
for tweet in mentions:
    # if 'render' in tweet.text:
        thread = []
        users_to_names = {} # This will serve to link @display_names with usernames
        counter = Counter()
        current_tweet = tweet
        while current_tweet.in_reply_to_status_id_str:
            current_tweet = api.get_status(current_tweet.in_reply_to_status_id_str)
            sanitize_tweet(current_tweet)
            users_to_names[current_tweet.author.screen_name] = current_tweet.author.name
            counter.update({current_tweet.author.screen_name: 1})  
            thread.insert(0, Comment(current_tweet))
        most_common = [users_to_names[t[0]] for t in counter.most_common()]
        characters = anim.get_characters(most_common)
        anim.comments_to_scene(thread, characters, output_filename=tweet.id_str + '.mp4')
        uploaded_media = api.media_upload(tweet.id_str + '.mp4')
        api.update_status('@' + tweet.in_reply_to_screen_name + ' ', in_reply_to_status_id=tweet.id_str, media_ids=[uploaded_media.media_id_string])
# if len(mentions) > 0:
#     with open('id.txt', 'w') as idFile:
#         idFile.write(mentions[0].id_str)