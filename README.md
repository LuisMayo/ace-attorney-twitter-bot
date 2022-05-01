# Ace Attorney Mastodon Bot
 Fork of [Ace Attorney Twitter bot](https://github.com/LuisMayo/ace-attorney-twitter-bot) that turns threads into Ace Attorney scenes, adapted for Mastodon and with "hate" detection removed



## Getting Started

### Prerequisites

 - Everything included in [/objection_engine/Readme.md](https://github.com/LuisMayo/objection_engine/blob/main/README.md#prerequisites).
 - Mastodon account (Pleroma should work, but it's not tested)
 - [pipenv](https://pipenv.pypa.io/en/latest/)


### Installing

Clone the repository with submodules

```
git clone --recursive https://github.com/matrix07012/ace-attorney-mastodon-bot.git
```
Install dependencies of this repo and the child repo. Refer to [objection engine's install instructions](https://github.com/LuisMayo/objection_engine/blob/main/README.md#installing) for any problems you may encounter
``` bash
python -m pipenv install
```
Copy settings-dummy.py as settings.py and set INSTANCE_URL, LOGIN, PASSWORD, and ADMIN in it

Start the project
`python main.py`

#### Note about Linux systems
In Linux it may be a bit harder to set the enviorenment properly. More specifically it may be hard to install required codecs.
If having a codec problem (like "couldn't find codec for id 27") you may need to compile ffmpeg and opencv by yourself.
You should be good using these guides (tested on Ubuntu with success and on Debian without success)
  - [FFMPEG compilation guide](https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu)
  - [Opencv compilation guide](https://docs.opencv.org/master/d2/de6/tutorial_py_setup_in_ubuntu.html)

## Contributing
Since this is a tiny project we don't have strict rules about contributions. Just open a Pull Request to fix any of the project issues or any improvement you have percieved on your own. Any contributions which improve or fix the project will be accepted as long as they don't deviate too much from the project objectives. If you have doubts about whether the PR would be accepted or not you can open an issue before coding to ask for my opinion
