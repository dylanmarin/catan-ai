# TODO

NEXT:
making moves on your turn

todo:
HIGH:
making moves

MEDIUM: 
evaluate opponent settlement and put it in robber placement
AI discarding resources
resource synergy of a settlement
Fix drawing in between placing settlements. something is up

LOW:
Fallback for if none of our logical options for placing the robber works
Deciding not to play a robber when blocked
Counting resources in bank before dealing out cards
Bayesian inference on unplayed cards


COMPLETED:

4/10
- finish robber placement function
- function for checking if it is possible to get resource through trading with bank/ports
- outline of goal utility function

4/9:
- initial road placement (naively in direction of next desired settlement)
- initial impl for whether we should place a knight (both for before rolling and for after)
- most of robber placement function

4/7:
- seed the random for testing
- road placement


4/5:
- make font a bit more readable in gameView.py
- in player.py make the PLAYER has placed a settlement message more readable
- added base evaluateSettlementFunction in dylanAIPlayer.py
- basic initial settlement evaluation
- AI initial resource desire priority
- port evaluation and port desire variable
- add diversity evaluation for settlements





## Project Changes
- catanGame.py -rerouted function calls to use my ai and take in any number of players and any number of ai players
- dylanAIPlayer.py -implementation of my ai implementation


## 