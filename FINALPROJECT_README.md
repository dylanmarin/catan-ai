# TODO
NEXT:
offer a trade to other ai. least desired card for most desired card
accept a trade from another ai




make it point initial road to direciton of next best settlement they EXPECT to have. ie. first player points to 8th best settlement spot (6 picks before their next, plus they will have placed another before this intial settlement could theoretically expand)

backlog:

MEDIUM: 
Fallback for if none of our logical options for placing the robber works
implement resource synergy of a settlement
Fix drawing in between placing settlements. something is not right
Deciding not to play a robber when blocked
have monopoly not just choose the resource that has the most cards, choose the resource that would provide the most production of a desired resource


LOW:
make year of plently look past just whether or not it helps with the current item
make trading ui on screen
Bayesian inference on unplayed cards
Counting resources in bank before dealing out cards

NOTES:
search "IMPROVEMENT" for improvements that aren't TODO's


COMPLETED:

4/16
- play road building if it can’t build a road but wants to
- using year of plenty instead of trading
- playing mono or road building
- get opponent resource count
- check if can build item with monopoly played
- check if can build with hypothetical additional resources
- made it so that road desire didnt consider possible settlements if it used all 5 settlements in order to make cities more valuable
- fixed bugs related to the remaining dev cards in the stack (trying to buy when none are left)
- 


4/13
- remove goals that actually would break the our resources for the current goal if built
    - ie if we wanna build a settlement, only remove dev card if it would mean we lose one of the items we need
- robber block winning player's tile that is shared with the most people ie produces the most production output 
    - block most common resource if all opponents are tied

4/12
- choose number of opponents (always 1vX) and choose which positioin you play in
- updated game to hide opponents cards opotionally
- greatly improved road placement function
- used new road placement function to place intiial road
- updated port evaluation to only care about ports we dont already have
- updated settlement desire to have some initial value to boost it since it gives us VPs that we need to win


4/11
- road / settlement / city / buy dev desire
- settlement placement / city placement
- rough draft of road placement. doens't currently play for longest road, only for going towards nearest good settlement
- more of move function implemented, trading for current goal and prioritizing saving cards when possible
- discarding resources

4/10
- finish robber placement function
- function for checking if it is possible to get resource through trading with bank/ports
- outline of goal utility function
- outlined utility functions definitions
- outlined move function overall flow some more


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