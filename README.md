# Ace Attorney twitter Bot
 Twitter bot that turns comment chains into ace attorney scenes. Inspired by and using https://github.com/micah5/ace-attorney-reddit-bot
 
## Getting Started

### Prerequisites

 - Python 3
 - Twitter Credentials.
 - Ace Attorney data. Download it [here](https://drive.google.com/drive/folders/16zqMXmAoUWlWNKhs6LRvrbHCE_1xt3Hi?usp=sharing) and put them in `./assets/`
 
 
### Installing

Clone the repository with submodules

```
git clone --recursive https://github.com/LuisMayo/ace-attorney-twitter-bot
```
Install dependencies of this repo and the child repo
``` bash
python -m pip install -r requirements.txt
python -m pip install -r ace-attorney-reddit-bot/requirements.txt
```
Copy keys-dummy.json into keys.json and fill the required settings with the access keys you should've obtained from Twitter's Developer portal

Start the project
`python main.py`

## Contributing
Since this is a tiny project we don't have strict rules about contributions. Just open a Pull Request to fix any of the project issues or any improvement you have percieved on your own. Any contributions which improve or fix the project will be accepted as long as they don't deviate too much from the project objectives. If you have doubts about whether the PR would be accepted or not you can open an issue before coding to ask for my opinion
