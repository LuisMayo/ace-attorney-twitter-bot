import sys
import json
sys.path.insert(0, './ace-attorney-reddit-bot')
import anim
from munch import munchify

authors = json.loads(sys.argv[1])
comments = json.loads(sys.argv[2])
# Dict != object
for idx, val in enumerate(comments):
    comments[idx] = munchify(val)
# print(comments[0].author)
filename = sys.argv[3]
characters = anim.get_characters(authors)
anim.comments_to_scene(comments, characters, output_filename=filename)