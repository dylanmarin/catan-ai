# Settlers of Catan
# Gameplay class with pygame

from board import *
from gameView import *
from player import *
from dylanAIPlayer import *
import queue
import numpy as np
import sys
import pygame
import time

# Catan gameplay class definition


class catanGame():
    # Create new gameboard
    def __init__(self):
        print("Initializing Settlers of Catan Board...")
        self.board = catanBoard()

        # Game State variables
        self.gameOver = False
        self.maxPoints = 10
        self.numPlayers = 0
        self.player_position = -1
        self.numAIPlayers = -1
        self.hide_ai_cards = False
        self.play_without_human = False

        # '''
        # DYLAN: Adjusted it to take in a number of opponents:
        while (self.numPlayers not in [1, 2, 3, 4]):
            try:
                self.numPlayers = int(
                    input("Enter Number of AI opponents (1, 2, or 3): ")) + 1
            except:
                print("Please input a valid number")

        if not self.play_without_human:
            while (self.player_position not in list(range(self.numPlayers))):
                try:
                    self.player_position = int(
                        input("Enter position [1-{}] (type -1 for random number): ".format(self.numPlayers))) - 1
                    
                    if self.player_position == -2:
                        self.player_position = np.random.randint(0, self.numPlayers)

                except:
                    print("Please input a valid number")
        else:
            self.numPlayers -= 1
        # '''

        '''
        while (self.numPlayers not in [1, 2, 3, 4]):
            try:
                self.numPlayers = int(
                    input("Enter Number of Players (2, 3, or 4): "))
            except:
                print("Please input a valid number")

        while (self.numAIPlayers > self.numPlayers or self.numAIPlayers < 0):
            try:
                self.numAIPlayers = int(
                    input("Enter Number of AI players. {} at most: ".format(self.numPlayers)))
            except:
                print("Please input a valid number")
        '''

        print("Initializing game with {} players...".format(self.numPlayers))
        print("Note that Player 1 goes first, Player 2 second and so forth.")

        # Initialize blank player queue and initial set up of roads + settlements
        self.playerQueue = queue.Queue(self.numPlayers)
        self.gameSetup = True  # Boolean to take care of setup phase

        # Initialize boardview object
        self.boardView = catanGameView(self.board, self)

        # Run functions to view board and vertex graph
        # self.board.printGraph()

        # Functiont to go through initial set up
        self.build_initial_settlements()

        # Display initial board
        self.boardView.displayGameScreen()

    # Function to initialize players + build initial settlements for players

    def build_initial_settlements(self):
        # Initialize new players with names and colors
        playerColors = ['black', 'blue', 'magenta4', 'orange1']

        '''
        NOTE: adding in AI players first so that I can see where they place when given the choice
        '''

        translated_player_colors = ['Black', 'Blue', 'Purple', 'Orange']

        # '''
        for i in range(self.numPlayers):
            

            if i == self.player_position:
                # TODO take player input again
                # playerNameInput = input("Enter Player {} name: ".format(i+1))
                # playerNameInput = "Player-{}".format(i + 1)
                playerNameInput = "YOU"
                print("Added new Player: {}".format(playerNameInput))
                newPlayer = player(
                    playerNameInput, playerColors[i], self.maxPoints)
                self.playerQueue.put(newPlayer)
            else: 
                # add AI player
                # test_AI_player = dylanAIPlayer(
                #     'AI-{}'.format(i+1), playerColors[i], self.maxPoints)
                test_AI_player = dylanAIPlayer(
                    'AI-{}'.format(translated_player_colors[i]), playerColors[i], self.maxPoints)
                test_AI_player.updateAI(self)
                self.playerQueue.put(test_AI_player)
        # '''



        '''
        # add in AI players first
        for i in range(self.numAIPlayers):
            test_AI_player = dylanAIPlayer(
                'AI-{}'.format(i+1), playerColors[i], self.maxPoints)
            test_AI_player.updateAI(self)
            self.playerQueue.put(test_AI_player)

        for i in range(self.numPlayers - self.numAIPlayers):
            # TODO take player input again
            # playerNameInput = input("Enter Player {} name: ".format(i+1))
            playerNameInput = "Player-{}".format(i + 1)
            newPlayer = player(playerNameInput, playerColors[i+(self.numAIPlayers)], self.maxPoints)
            self.playerQueue.put(newPlayer)
        '''

        playerList = list(self.playerQueue.queue)

        self.boardView.displayGameScreen()  # display the initial gameScreen
        print("Displaying Initial GAMESCREEN!")

        # Build Settlements and roads of each player forwards
        for player_i in playerList:
            if (player_i.isAI):
                # AI player calls initial setup to place its first settlements and roads
                self.boardView.displayGameScreen()
                player_i.initial_setup(self.board)
                time.sleep(0.2)
                self.boardView.displayGameScreen()

            else:
                time.sleep(0.1)
                self.build(player_i, 'SETTLE')
                self.boardView.displayGameScreen()

                time.sleep(0.1)
                self.build(player_i, 'ROAD')
                self.boardView.displayGameScreen()

        # Build Settlements and roads of each player reverse
        playerList.reverse()
        for player_i in playerList:
            if (player_i.isAI):
                player_i.initial_setup(self.board)
                time.sleep(0.2)
                self.boardView.displayGameScreen()
                pygame.display.update()

            else:
                time.sleep(0.1)
                self.build(player_i, 'SETTLE')
                self.boardView.displayGameScreen()

                time.sleep(0.1)
                self.build(player_i, 'ROAD')
                self.boardView.displayGameScreen()

            # Initial resource generation
            # check each adjacent hex to latest settlement
            for adjacentHex in self.board.boardGraph[player_i.buildGraph['SETTLEMENTS'][-1]].adjacentHexList:
                resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                if (resourceGenerated != 'DESERT'):
                    player_i.resources[resourceGenerated] += 1
                    print("{} collects 1 {} from Settlement".format(
                        player_i.name, resourceGenerated))

        self.gameSetup = False

        return

    # Generic function to handle all building in the game - interface with gameView

    # DYLAN: added raodbuilder flag because currently it still tries to use resources to
    def build(self, player, build_flag, road_builder=False):
        if (build_flag == 'ROAD'):  # Show screen with potential roads
            if (self.gameSetup):
                potentialRoadDict = self.board.get_setup_roads(player)
            else:
                potentialRoadDict = self.board.get_potential_roads(player)

            roadToBuild = self.boardView.buildRoad_display(
                player, potentialRoadDict)
            if (roadToBuild != None):
                player.build_road(
                    roadToBuild[0], roadToBuild[1], self.board, road_builder=road_builder)

        if (build_flag == 'SETTLE'):  # Show screen with potential settlements
            if (self.gameSetup):
                potentialVertexDict = self.board.get_setup_settlements(player)
            else:
                potentialVertexDict = self.board.get_potential_settlements(
                    player)

            vertexSettlement = self.boardView.buildSettlement_display(
                player, potentialVertexDict)
            if (vertexSettlement != None):
                player.build_settlement(vertexSettlement, self.board)

        if (build_flag == 'CITY'):
            potentialCityVertexDict = self.board.get_potential_cities(player)
            vertexCity = self.boardView.buildSettlement_display(
                player, potentialCityVertexDict)
            if (vertexCity != None):
                player.build_city(vertexCity, self.board)

    # Wrapper Function to handle robber functionality

    def robber(self, player):
        potentialRobberDict = self.board.get_robber_spots()
        print("Move Robber!")

        hex_i, playerRobbed = self.boardView.moveRobber_display(
            player, potentialRobberDict)
        player.move_robber(hex_i, self.board, playerRobbed)

    # Function to roll dice

    def rollDice(self):
        dice_1 = np.random.randint(1, 7)
        dice_2 = np.random.randint(1, 7)
        diceRoll = dice_1 + dice_2
        print("Dice Roll = ", diceRoll, "{", dice_1, dice_2, "}")

        self.boardView.displayDiceRoll(diceRoll)

        return diceRoll

    # Function to update resources for all players
    def update_playerResources(self, diceRoll, currentPlayer):
        self.boardView.displayDiceRoll(diceRoll)

        if (diceRoll != 7):  # Collect resources if not a 7
            # First get the hex or hexes corresponding to diceRoll
            hexResourcesRolled = self.board.getHexResourceRolled(diceRoll)
            #print('Resources rolled this turn:', hexResourcesRolled)

            # Check for each player
            for i in range(self.numPlayers): 
                player_i = list(self.playerQueue.queue)[i]
                # Check each settlement the player has
                for settlementCoord in player_i.buildGraph['SETTLEMENTS']:
                    # check each adjacent hex to a settlement
                    for adjacentHex in self.board.boardGraph[settlementCoord].adjacentHexList:
                        # This player gets a resource if hex is adjacent and no robber
                        if (adjacentHex in hexResourcesRolled and self.board.hexTileDict[adjacentHex].robber == False):
                            resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                            player_i.resources[resourceGenerated] += 1
                            print("{} collects 1 {} from Settlement".format(
                                player_i.name, resourceGenerated))

                # Check each City the player has
                for cityCoord in player_i.buildGraph['CITIES']:
                    # check each adjacent hex to a settlement
                    for adjacentHex in self.board.boardGraph[cityCoord].adjacentHexList:
                        # This player gets a resource if hex is adjacent and no robber
                        if (adjacentHex in hexResourcesRolled and self.board.hexTileDict[adjacentHex].robber == False):
                            resourceGenerated = self.board.hexTileDict[adjacentHex].resource.type
                            player_i.resources[resourceGenerated] += 2
                            print("{} collects 2 {} from City".format(
                                player_i.name, resourceGenerated))

                # DYLAN UPDATING PRINTING TO HIDE OPPONENT CARDS
                if not self.hide_ai_cards or i == self.player_position:
                    player_i.print_player_info(resources=True, true_vp=True, dev_cards=True, buildings_left=True, road_and_army_info=True)
                else:
                    player_i.print_player_info(resources=False, true_vp=False, dev_cards=False, buildings_left=False, road_and_army_info=True)


        # Logic for a 7 roll
        else:
            # Implement discarding cards
            # Check for each player
            for player_i in list(self.playerQueue.queue):
                if (player_i.isAI):
                    player_i.discard_cards(self.board)

                else:
                    # Player must discard resources
                    player_i.discardResources()

            # Logic for robber
            if (currentPlayer.isAI):
                currentPlayer.place_robber(self.board)
            else:
                time.sleep(0.1)
                self.robber(currentPlayer)
                self.boardView.displayGameScreen()  # Update back to original gamescreen                    
                
        # print current_player last always
        if not currentPlayer.isAI or not self.hide_ai_cards:
            currentPlayer.print_player_info()
        else:
            currentPlayer.print_player_info(resources=False, true_vp=False, dev_cards=False, buildings_left=False, road_and_army_info=True)



    # function to check if a player has the longest road - after building latest road

    def check_longest_road(self, player_i):
        if (player_i.maxRoadLength >= 5):  # Only eligible if road length is at least 5
            longestRoad = True
            for p in list(self.playerQueue.queue):
                # Check if any other players have a longer road
                if (p.maxRoadLength >= player_i.maxRoadLength and p != player_i):
                    longestRoad = False

            # if player_i takes longest road and didn't already have longest road
            if (longestRoad and player_i.longestRoadFlag == False):
                # Set previous players flag to false and give player_i the longest road points
                prevPlayer = ''
                for p in list(self.playerQueue.queue):
                    if (p.longestRoadFlag):
                        p.longestRoadFlag = False
                        p.victoryPoints -= 2
                        p.visibleVictoryPoints -= 2
                        prevPlayer = 'from Player ' + p.name

                player_i.longestRoadFlag = True
                p.visibleVictoryPoints += 2
                player_i.victoryPoints += 2

                print("Player {} takes Longest Road {}".format(
                    player_i.name, prevPlayer))

    # function to check if a player has the largest army - after playing latest knight
    def check_largest_army(self, player_i):
        if (player_i.knightsPlayed >= 3):  # Only eligible if at least 3 knights are player
            largestArmy = True
            for p in list(self.playerQueue.queue):
                # Check if any other players have more knights played
                if (p.knightsPlayed >= player_i.knightsPlayed and p != player_i):
                    largestArmy = False

            # if player_i takes largest army and didn't already have it
            if (largestArmy and player_i.largestArmyFlag == False):
                # Set previous players flag to false and give player_i the largest points
                prevPlayer = ''
                for p in list(self.playerQueue.queue):
                    if (p.largestArmyFlag):
                        p.largestArmyFlag = False
                        p.victoryPoints -= 2
                        p.visibleVictoryPoints -= 2
                        prevPlayer = 'from Player ' + p.name

                player_i.largestArmyFlag = True
                player_i.victoryPoints += 2
                player_i.visibleVictoryPoints += 2

                print("Player {} takes Largest Army {}".format(
                    player_i.name, prevPlayer))

    # Function that runs the main game loop with all players and pieces

    def playCatan(self):
        # self.board.displayBoard() #Display updated board

        while (self.gameOver == False):

            # Loop for each player's turn -> iterate through the player queue
            for currPlayer in self.playerQueue.queue:

                print(
                    "---------------------------------------------------------------------------")
                print("Current Player:", currPlayer.name)

                turnOver = False  # boolean to keep track of turn
                diceRolled = False  # Boolean for dice roll status

                # Update Player's dev card stack with dev cards drawn in previous turn and reset devCardPlayedThisTurn
                currPlayer.updateDevCards()
                currPlayer.devCardPlayedThisTurn = False

                while (turnOver == False):

                    if (currPlayer.isAI):
                        # time.sleep(0.3)
                        
                        # check if AI wants to play a knight before rolling
                        if currPlayer.should_play_knight_before_rolling(self.board):
                            print("{} is playing a knight".format(
                                currPlayer.name))
                            currPlayer.play_knight(self.board)

                        # roll Dice
                        diceNum = self.rollDice()
                        diceRolled = True
                        self.update_playerResources(diceNum, currPlayer)

                        self.boardView.displayDiceRoll(diceNum)

                        # TODO: THIS IS WHERE THE AI TURN IS MADE
                        # AI Player makes all its moves
                        currPlayer.move(self.board)

                        # Check if AI player gets longest road/largest army and update Victory points
                        self.check_longest_road(currPlayer)
                        self.check_largest_army(currPlayer)
                        
                        if self.hide_ai_cards:
                            currPlayer.print_player_info(resources=False, true_vp=False, dev_cards=False, buildings_left=False, road_and_army_info=True)
                        else:
                            currPlayer.print_player_info()
                            
                        self.boardView.displayGameScreen()  # Update back to original gamescreen
                        turnOver = True

                    else:  # Game loop for human players
                        for e in pygame.event.get():  # Get player actions/in-game events
                            # print(e)
                            if e.type == pygame.QUIT:
                                sys.exit(0)

                            # Check mouse click in rollDice
                            if (e.type == pygame.MOUSEBUTTONDOWN):
                                # Check if player rolled the dice
                                if (self.boardView.rollDice_button.collidepoint(e.pos)):
                                    if (diceRolled == False):  # Only roll dice once
                                        diceNum = self.rollDice()
                                        diceRolled = True

                                        self.boardView.displayDiceRoll(diceNum)
                                        # Code to update player resources with diceNum
                                        self.update_playerResources(
                                            diceNum, currPlayer)

                                # Check if player wants to build road
                                if (self.boardView.buildRoad_button.collidepoint(e.pos)):
                                    # Code to check if road is legal and build
                                    if (diceRolled == True):  # Can only build after rolling dice
                                        self.build(currPlayer, 'ROAD')
                                        self.boardView.displayGameScreen()  # Update back to original gamescreen

                                        # Check if player gets longest road and update Victory points
                                        self.check_longest_road(currPlayer)
                                        # Show updated points and resources
                                        currPlayer.print_player_info()

                                # Check if player wants to build settlement
                                if (self.boardView.buildSettlement_button.collidepoint(e.pos)):
                                    # Can only build settlement after rolling dice
                                    if (diceRolled == True):
                                        self.build(currPlayer, 'SETTLE')
                                        self.boardView.displayGameScreen()  # Update back to original gamescreen
                                        # Show updated points and resources
                                        currPlayer.print_player_info()

                                # Check if player wants to build city
                                if (self.boardView.buildCity_button.collidepoint(e.pos)):
                                    if (diceRolled == True):  # Can only build city after rolling dice
                                        self.build(currPlayer, 'CITY')
                                        self.boardView.displayGameScreen()  # Update back to original gamescreen
                                        # Show updated points and resources
                                        currPlayer.print_player_info()

                                # Check if player wants to draw a development card
                                if (self.boardView.devCard_button.collidepoint(e.pos)):
                                    if (diceRolled == True):  # Can only draw devCard after rolling dice
                                        currPlayer.draw_devCard(self.board, show_card=True)
                                        # Show updated points and resources
                                        currPlayer.print_player_info()
                                        print('Available Dev Cards:',
                                              currPlayer.devCards)

                                # Check if player wants to play a development card - can play devCard whenever after rolling dice
                                if (self.boardView.playDevCard_button.collidepoint(e.pos)):
                                    currPlayer.play_devCard(self)
                                    self.boardView.displayGameScreen()  # Update back to original gamescreen

                                    # Check for Largest Army and longest road
                                    self.check_largest_army(currPlayer)
                                    self.check_longest_road(currPlayer)
                                    # Show updated points and resources
                                    currPlayer.print_player_info()

                                # Check if player wants to trade with the bank
                                if (self.boardView.tradeBank_button.collidepoint(e.pos)):
                                    currPlayer.initiate_trade(self.board, self, 'BANK')
                                    # Show updated points and resources
                                    currPlayer.print_player_info()

                                # Check if player wants to trade with another player
                                if (self.boardView.tradePlayers_button.collidepoint(e.pos)):
                                    currPlayer.initiate_trade(self.board, self, 'PLAYER')
                                    # Show updated points and resources
                                    currPlayer.print_player_info()

                                # Check if player wants to end turn
                                if (self.boardView.endTurn_button.collidepoint(e.pos)):
                                    if (diceRolled == True):  # Can only end turn after rolling dice
                                        print("Ending Turn!")
                                        turnOver = True  # Update flag to nextplayer turn

                    if self.play_without_human:
                        time.sleep(1)
                    # Update the display
                    # self.displayGameScreen(None, None)
                    pygame.display.update()

                    # Check if game is over
                    if currPlayer.victoryPoints >= self.maxPoints:
                        self.gameOver = True
                        self.turnOver = True
                        print("====================================================")
                        print("PLAYER {} WINS!".format(currPlayer.name))
                        print("Exiting game in 10 seconds...")
                        break

                if (self.gameOver):
                    startTime = pygame.time.get_ticks()
                    runTime = 0
                    while (runTime < 10000):  # 10 second delay prior to quitting
                        runTime = pygame.time.get_ticks() - startTime

                    break


# Initialize new game and run
newGame = catanGame()
newGame.playCatan()

for i in range(99999999999):
    a = 1
# while (True):
#     newGame.boardView.displayGameScreen()
#     pygame.display.update()
#     a = 1
# newGame.playCatan()
