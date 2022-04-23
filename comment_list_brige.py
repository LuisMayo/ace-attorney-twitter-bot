import requests
from objection_engine.beans.comment import Comment as obj_comment
from objection_engine.beans.text import is_renderable

class Comment:
    def __init__(self, tweet):
        # check if username is renderable, if not, use their "screen_name"
        if is_renderable(tweet.user.name):
            self.author_name = tweet.user.name
        else:
            self.author_name = f"@{tweet.user.screen_name}"
        self.author_id = tweet.user.id_str
        self.body = tweet.full_text
        self.evidence = None
        if (hasattr(tweet,'extended_entities') and tweet.extended_entities is not None
        and 'media' in tweet.extended_entities and len(tweet.extended_entities['media']) > 0):
            url = tweet.extended_entities['media'][0]['media_url_https'] + '?format=png&name=small'
            name = tweet.extended_entities['media'][0]['media_url_https'].split('/')[-1] + '.png'
            response = requests.get(url)
            with open(name, 'wb') as file:
                file.write(response.content)
            self.evidence = name
    def to_message(self) -> obj_comment:
        return obj_comment(user_id=self.author_id, user_name = self.author_name, text_content=self.body, evidence_path=self.evidence)