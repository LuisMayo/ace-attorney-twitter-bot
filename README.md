# Ace Attorney twitter Bot
 Twitter bot that turns comment chains into ace attorney scenes. Inspired by and using https://github.com/micah5/ace-attorney-reddit-bot
 Currently being executed on [@aceCourtBot](https://twitter.com/aceCourtBot?s=09)

 Check also the [Telegram](https://github.com/LuisMayo/ace-attorney-telegram-bot), [Discord](https://github.com/LuisMayo/ace-attorney-discord-bot) and [Reddit](https://github.com/micah5/ace-attorney-reddit-bot) bots!

## Getting Started

### Prerequisites

 - Everything included in [/objection_engine/Readme.md](https://github.com/LuisMayo/objection_engine/blob/main/README.md#prerequisites).
 - Twitter Credentials.


### Installing

Clone the repository with submodules

```
git clone --recursive https://github.com/LuisMayo/ace-attorney-twitter-bot
```
Install dependencies of this repo and the child repo. Refer to [objection engine's install instructions](https://github.com/LuisMayo/objection_engine/blob/main/README.md#installing) for any problems you may encounter
``` bash
python -m pip install -r requirements.txt
python -m pip install -r objection_engine/requirements.txt
```
Copy keys-dummy.json into keys.json and fill the required settings with the access keys you should've obtained from Twitter's Developer portal

Start the project
`python main.py`

#### Note about Linux systems
In Linux it may be a bit harder to set the enviorenment properly. More specifically it may be hard to install required codecs.
If having a codec problem (like "couldn't find codec for id 27") you may need to compile ffmpeg and opencv by yourself.
You should be good using these guides (tested on Ubuntu with success and on Debian without success)
  - [FFMPEG compilation guide](https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu)
  - [Opencv compilation guide](https://docs.opencv.org/master/d2/de6/tutorial_py_setup_in_ubuntu.html)

#### Note about MongoDB
By default Mongita is used for easier deployment, but administrators can opt in to use full MongoDB. Set the environment variable `ACE_MONGODB=1` for this and make sure MongoDB is installed on your machine.

## Contributing
Since this is a tiny project we don't have strict rules about contributions. Just open a Pull Request to fix any of the project issues or any improvement you have percieved on your own. Any contributions which improve or fix the project will be accepted as long as they don't deviate too much from the project objectives. If you have doubts about whether the PR would be accepted or not you can open an issue before coding to ask for my opinion
