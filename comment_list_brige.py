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
        self.body = soup.get_text().strip()
        extr_text = self.body

        # remove mentions from the start and end
        try:
            if extr_text[0] == '@':
                while extr_text[0] != ' ' or (extr_text[0] == ' ' and extr_text[1] == '@'):
                    if extr_text[0] == '\n':
                        break
                    extr_text = extr_text[1:]
                extr_text = extr_text[1:]

            last_at = extr_text.rfind('@')
            temp_str = extr_text[last_at:]
            while extr_text[last_at - 1] == ' ' and ' ' not in temp_str:
                extr_text = extr_text[:last_at - 1]
                last_at = extr_text.rfind('@')
                temp_str = extr_text[last_at:]

            self.body = extr_text
        except Exception as e:
            print(e)

        if len(self.body) == 0:
            self.body = "Presenting evidence"

        # get first attached picture
        if len(stat["media_attachments"]) > 0:
            first = stat["media_attachments"][0]
            if first["type"] == "image":
                url = first["url"]
                name = first["url"].split('/')[-1]
                try:
                    response = requests.get(url)
                    with open(name, 'wb') as file:
                        file.write(response.content)
                    self.evidence = name
                except Exception as e:
                    print(e)

    def to_message(self) -> obj_comment:
        return obj_comment(user_id=self.author_id, user_name=self.author_name, text_content=self.body,
                           evidence_path=self.evidence)
