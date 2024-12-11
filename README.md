# How to Install
1. Open Terminal
2. Make sure python is installed
	Mac: `python --version` or `python3 --version`
	Windows: `python --version ` or ` python -V`
	If not then install from python website
3. Place download into a folder and copy pathname:
	- Mac: on finder secondary click folder and hold option key, then `copy as pathname`
	- Go to terminal and run `cd 'pathname/you/copied'`
	- run `ls` and make sure you have these 4 files: 
	`README.md` `hand.py` `app.pp` `requirements.txt`
4. run `pip install -r requirements.txt` in terminal

#### How to run
`python3 app.py`
if a window appears then you did it

#### How to set up MIDI Driver
###### Mac:
- Open Audio MIDI Setup
- click Window->Show MIDI Studio
- click on IAC Driver
- check "Device Online"
- Make sure its Port is "Bus1"

