# CatanAI

## Framework Overview
Read the project report for an in-depth description of how the code works. Otherwise you can refer to commenting and documentation within dylanAIPlayer.

Below is the description from the original repo:

Game functionality is implemented in the following modules:
1. ```hexTile.py``` - Implements the hexagonal tiles for the Catan board, with a complete graph representation outline for vertices and edges. Mathematical representation easy drawing of hexagonal grids and pixel math is implemented in ```hexLib.py```, adapted from  http://www.redblobgames.com/grids/hexagons/
2. ```board.py``` - Base class to implement the board, and board related functionality such as building roads, settlements and cities. 
2. ```board.py``` - Base class to implement the board, and board related functionality such as building roads, settlements and cities. 
3. ```player.py`` - Base class to implement player functionality.
4. ```catanGame.py``` and ```AIGame.py``` - Wrapper classes to interface game representation with GUI
5. ```gameView.py``` - Graphics class implemented to interface game mechanics with pygame-based GUI.


## Dylan Changes
1. ```dylanAIPlayer.py``` -  The AI Player inherits the player class and uses my own code to make decisions
2. ```board.py``` - I added random seeding for testing purposes. Also added some functions to help with road calculations
3. ```catanGame.py``` - Lots of changes in order to generate the right amount of AI players, and have my AI do the correct thing when it needed to
4. ```gameView.py``` - Some changes to graphics implementation to make it more legible
4. ```player.py``` - Some changes to allow better abstraction. Added print function to simplify repeated code
 

## Debug Tools:

1. Hide other players cards in ```catanGame.py``` set ```self.hide_ai_cards = True```. Currently set to False to help with debugging but really clutters the terminal
2. Hide/show move desire ```dylanAIPlayer.py``` within ```def move(self, board):``` set ```debug = True/False```. Set to false to clear up the terminal as much as possible but of all debug flags THIS is the most useful one. 
3. Change board random seed ```board.py``` very near the top set change value within ```np.random.seed()```
4. Various other functions have debug flags that can be set to True in ```dylanAIPlayer.py```


## Notes:
- You kind of have to be precise with your clicks. If you miss the road, it'll cancel building it, but just try again.
- Once you start a trade offer you have to finish making the offer. The original repo was like this and I didn't have time to make it nicer.
- If the game freezes, check the terminal, you probably have to discard or are being offered a trade.
- The screen kind of flashes and sometimes the items on it disappear. As far as I can tell this is an issue with the updateGameScreen function being called so many times in quick succession during all of the AI opponent refreshes. I tried to work around this by adding a quick time.sleep before each player's turn, though I inconsistently still had it occur during testing. 
- The AI all move at computer-speed, not human speed, so reading the logs is helpful to know what happened in the last 3 turns since ended yours
- Install pygame and run catanGame.py with python 3.10 to play

## References
Original repo: https://github.com/kvombatkere/Catan-AI