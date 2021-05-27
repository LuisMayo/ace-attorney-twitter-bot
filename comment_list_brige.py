import requests
from bs4 import BeautifulSoup
from objection_engine.beans.comment import Comment as obj_comment


class Comment:
    def __init__(self, stat):
        self.author_name = stat["account"]["username"]
        self.author_id = stat["account"]["id"]
        self.body = stat["content"]
        self.evidence = None

        soup = BeautifulSoup(stat["content"])
        self.body = soup.get_text()

        if len(stat["media_attachments"]) > 0:
            first = stat["media_attachments"][0]
            if first["type"] == "image":
                url = first["url"]
                name = first["url"].split('/')[-1]
                response = requests.get(url)
                with open(name, 'wb') as file:
                    file.write(response.content)
                self.evidence = name

    def to_message(self) -> obj_comment:
        return obj_comment(user_id=self.author_id, user_name=self.author_name, text_content=self.body,
                           evidence_path=self.evidence)
