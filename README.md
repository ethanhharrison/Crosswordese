## How to run/play
1. Clone either the ```crossword-game``` or ```crossword-solver``` branch.
2. Create a python virtual environment with the command ```python -m venv venv```
3. Activate the venv using ```source venv/bin/activate``` on Mac or ```venv\Scripts\activate``` on Windows
4. Install required directories with ```pip3 install -r requirements.txt```
5. Download the NYT crossword JSONs from https://github.com/doshea/nyt_crosswords.git and add that master folder to your cloned directory.
6. Create a python file named ```config.py``` and add your OpenAi api key as ```OPENAI_API_KEY="YOUR_KEY_HERE"```
7. Run ```python3 crossword_game.py``` in the terminal
8. Have fun!
