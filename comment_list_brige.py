import requests
from objection_engine.beans.comment import Comment as obj_comment

class Comment:
    def __init__(self, stat):
        self.author_name = stat["account"]["display_name"]
        self.author_id = stat["account"]["id"]
        self.body = stat["content"]
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