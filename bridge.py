import sys
import json
sys.path.insert(0, './ace-attorney-reddit-bot')
import anim
authors = json.loads(sys.argv[1])
characters = anim.get_characters(authors)
print(characters)