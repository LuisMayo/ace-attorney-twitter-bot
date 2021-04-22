import requests

class Comment:
  def __init__(self, tweet):
    self.author = Author(tweet.user.name)
    self.body = tweet.full_text
    if (len(self.body) == 0):
        self.body = '...'
    self.score = 0
    if (hasattr(tweet,'extended_entities') and tweet.extended_entities is not None
    and 'media' in tweet.extended_entities and len(tweet.extended_entities['media']) > 0):
        url = tweet.extended_entities['media'][0]['media_url_https'] + '?format=png&name=small'
        name = tweet.extended_entities['media'][0]['media_url_https'].split('/')[-1] + '.png'
        response = requests.get(url)
        with open(name, 'wb') as file:
            file.write(response.content)
        self.evidence = name

class Author:
    def __init__(self, name):
        self.name = name
