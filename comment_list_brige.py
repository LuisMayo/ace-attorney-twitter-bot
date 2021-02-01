class Comment:
  def __init__(self, tweet):
    self.author = Author(tweet.user.name)
    self.body = tweet.full_text
    self.score = 0

class Author:
    def __init__(self, name):
        self.name = name