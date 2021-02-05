class Comment:
  def __init__(self, tweet):
    self.author = Author(tweet.user.name)
    self.body = tweet.full_text
    if (len(self.body) == 0):
        self.body = '...'
    self.score = 0

class Author:
    def __init__(self, name):
        self.name = name
