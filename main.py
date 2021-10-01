from datetime import datetime, timezone
import sys
import json
from update_queue_lenght import update_queue_length
sys.path.append('./objection_engine')
sys.path.append('./video-splitter')
from collections import Counter 
import tweepy
import re
import time
import os
from persistqueue import Queue
import threading
import random
import settings
from hatesonar import Sonar
from better_profanity import profanity
from comment_list_brige import Comment
from objection_engine.renderer import render_comment_list
splitter = __import__("ffmpeg-split")

sonar = Sonar()
mention_queue = Queue('queue')
delete_queue = Queue('delete')
profanity.load_censor_words_from_file('banlist.txt')



def sanitize_tweet(tweet):
    tweet.full_text = re.sub(r'^(@\S+ )+', '', tweet.full_text)
    tweet.full_text = re.sub(r'(https)\S*', '(link)', tweet.full_text)
    sonar_prediction = sonar.ping(tweet.full_text)
    hate_classification = next((x for x in sonar_prediction['classes']  if x['class_name'] == 'hate_speech'), None)
    if (hate_classification["confidence"] > 0.6):
        tweet.full_text = '...'
    tweet.full_text = profanity.censor(tweet.full_text)
    return hate_classification["confidence"] > 0.8

def update_id(id):
    with open('id.txt', 'w') as idFile:
        idFile.write(id)

def postVideoTweet(reply_id, filename):
    uploaded_media = api.media_upload(filename, media_category='TWEET_VIDEO')
    while (uploaded_media.processing_info['state'] == 'pending'):
        time.sleep(uploaded_media.processing_info['check_after_secs'])
        uploaded_media = api.get_media_upload_status(uploaded_media.media_id_string)
    time.sleep(10)
    return api.update_status('Your video is ready. Do you want it removed? contact @/LuisMayoV', in_reply_to_status_id=reply_id, auto_populate_reply_metadata = True, media_ids=[uploaded_media.media_id_string])


def check_mentions():
    global lastId
    global mention_queue
    global render_regex
    while True:
        try:
            mentions = api.mentions_timeline(count='200', tweet_mode="extended") if lastId == None else api.mentions_timeline(since_id=lastId, count='200', tweet_mode="extended")
            if len(mentions) > 0:
                lastId = mentions[0].id_str
                for tweet in mentions[::-1]:
                    if re.search(render_regex, tweet.full_text) is not None:
                        mention_queue.put(tweet)
                        print(mention_queue.qsize())
                    if 'delete' in tweet.full_text:
                        delete_queue.put(tweet)
                update_id(lastId)
        except Exception as e:
            print(e)
        time.sleep(20)

def process_deletions():
    global delete_queue


def process_tweets():
    global mention_queue
    global update_queue_params
    global me
    while True:
        try:
            tweet = mention_queue.get()
            update_queue_params['last_time'] = tweet.created_at
            thread = []
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
                    api.update_status('The music argument format is incorrect. The posibilities are: \nPWR: Phoenix Wright Ace Attorney \nJFA: Justice for All \nTAT: Trials and Tribulations \nrnd: Random', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
                except Exception as musicerror:
                    print(musicerror)
            else:
                # In the case of Quotes I have to check for its presence instead of whether its None because Twitter API designers felt creative that week
                i = 0
                # If we have 2 hate detections we stop rendering the video all together
                hate_detections = 0
                while (current_tweet is not None) and (current_tweet.in_reply_to_status_id_str or hasattr(current_tweet, 'quoted_status_id_str')):
                    try:
                        current_tweet = api.get_status(current_tweet.in_reply_to_status_id_str or current_tweet.quoted_status_id_str, tweet_mode="extended")
                        # Refusing to render zone
                        if re.search(render_regex, current_tweet.full_text) is not None and any(user['id_str'] == me for user in current_tweet.entities['user_mentions']):
                            api.update_status('I\'m sorry. Calling the bot several times in the same thread is not allowed', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
                            break
                        if sanitize_tweet(current_tweet):
                            hate_detections += 1
                        if hate_detections >= 2:
                            api.update_status('I\'m sorry. The thread may contain unwanted topics and I refuse to render them.', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
                            clean(thread, None, [])
                            thread = []
                            break
                    # End of refusing to render zone
                        thread.insert(0, Comment(current_tweet).to_message())
                        i += 1
                        if (current_tweet is not None and i >= settings.MAX_TWEETS_PER_THREAD):
                            current_tweet = None
                            api.update_status(f'Sorry, the thread was too long, I\'ve only retrieved {i} tweets', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
                    except tweepy.error.TweepError as e:
                        try:
                            api.update_status('I\'m sorry. I wasn\'t able to retrieve the full thread. Deleted tweets or private accounts may exist', in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
                        except Exception as second_error:
                            print (second_error)
                        current_tweet = None
                if (len(thread) >= 1):
                    output_filename = tweet.id_str + '.mp4'
                    render_comment_list(thread, music_code= music_tweet, output_filename=output_filename)
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
                                api.update_status(str(e), in_reply_to_status_id=tweet.id_str, auto_populate_reply_metadata = True)
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
            if (hasattr(comment, 'evidence') and comment.evidence is not None):
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
me_response = api.me()
# render_regex = f'^ *@{me_response.screen_name} render'
render_regex = 'render'
me = me_response.id_str
update_queue_params = {
    'queue': mention_queue,
    'last_time': None,
    'api': api
}
producer = threading.Thread(target=check_mentions)
consumer = threading.Thread(target=process_tweets)
threading.Thread(target=process_tweets).start()
threading.Thread(target=update_queue_length, args=[update_queue_params]).start()
producer.start()
consumer.start()
