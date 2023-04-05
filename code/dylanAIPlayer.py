# Settlers of Catan
# Dylan AI class implementation

from board import *
from player import *
# from catanGame import *
import numpy as np

# Class definition for an AI player


class dylanAIPlayer(player):

    # Update AI player flag and resources
    # DYLAN: Added params to give initial preference to different resources
    def updateAI(self, ore=5, brick=5, wheat=5, wood=5, sheep=5, port_desire=1):
        self.isAI = True

        # Initialize resources with just correct number needed for set up (2 settlements and 2 road)
        # Dictionary that keeps track of resource amounts
        self.resources = {'ORE': 0, 'BRICK': 4,
                          'WHEAT': 2, 'WOOD': 4, 'SHEEP': 2}

        # DYLAN: Moved their diceRoll_expectation dict into a class var
        self.diceRoll_expectation = {2: 1, 3: 2, 4: 3, 5: 4,
                                     6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1, None: 0}

        # DYLAN: Added dicitonary of resource preferences to help tweak the ai on what to pick initially
        self.resourcePreferences = {
            'ORE': ore, 'BRICK': brick, 'WHEAT': wheat, 'WOOD': wood, 'SHEEP': sheep}

        # DYLAN:
        '''
        port desire is an real value from 0 to 1 representing how valuable a port is to the AI
        0 means ports add no value to the evaluation
        1 means a port is as valuable as the corresponding produciton points of the resource.
            ie. we have 4 points of production for sheep. a 2:1 sheep port would add equal value as a tile with two production points
                a 3:1 port is as valuable as all of our production points divided by 3
        2 means we like ports twice as much as the production points it provides, etc.
        '''
        self.port_desire = port_desire

        print("Added new AI Player: ", self.name)

    # Function to build an initial settlement - just choose random spot for now

    def initial_setup(self, board):

        # All possible vertices for initial placement. accounts for only valid spots to place
        possible_placements = {}
        for placement in board.get_setup_settlements(self).keys():
            possible_placements[placement] = 0

        for p in possible_placements.keys():
            possible_placements[p] = self.evaluateSettlement(board, p)

        # get the placement with the max value
        best_placement = max(possible_placements,
                             key=possible_placements.get)

        self.build_settlement(best_placement, board)

    # DYLAN: Added evaluate settlement function
    def evaluateSettlement(self, board, settlement_location):
        '''
        multiply production by desire for that production

        add rating of ports usable by this settlement to the rating

        '''

        total_rating = 0

        # Evaluate based on adjacent hexes
        for adjacentHex in board.boardGraph[settlement_location].adjacentHexList:
            resourceType = board.hexTileDict[adjacentHex].resource.type
            if (resourceType != 'DESERT'):
                numValue = board.hexTileDict[adjacentHex].resource.num

                # multiply production points by desire for that resuorce
                total_rating += self.diceRoll_expectation[numValue] * \
                    self.resourcePreferences[resourceType]

        # Evaluate nearby ports and add that rating to the total rating
        port = board.boardGraph[settlement_location].port
        if port:
            total_rating += self.evaluatePort(board, port, settlement_location)

        return total_rating

    def evaluatePort(self, board, port, hypothetical_settlement):
        # debug var
        debug = False

        total_value = 0

        # if it is a 2:1 port
        if port[:3] == "2:1":
            port_resource_type = port[4:]

            # want it to be proportional to production points but not too overpowered
            total_value += 0.5 * self.port_desire * \
                self.getProductionPoints(
                    board, port_resource_type, hypothetical_settlement)
        else:
            # if it is 3:1 add scaled down value proportional to total production points
            for resource_type in self.resources.keys():
                threeToOneRatio = 0.33 * self.port_desire
                total_value += threeToOneRatio * \
                    self.getProductionPoints(
                        board, resource_type, hypothetical_settlement)

        if debug:
            print("Eval for {} is {}".format(port, str(total_value)))

        return total_value

    def getProductionPoints(self, board, resource, hypothetical_settlement):
        # Return amount of hex of given resource times amount of ways to roll the number on each hex

        total_prod = 0

        # for each settlement
        for settlement in self.buildGraph["SETTLEMENTS"]:
            total_prod += self.getProductionPointsForSettlement(
                board, resource, settlement)

        if hypothetical_settlement:
            total_prod += self.getProductionPointsForSettlement(
                board, resource, hypothetical_settlement)

        return total_prod

    def getProductionPointsForSettlement(self, board, resource, settlement):
        '''
        given a settlement and a resource, return the production points that that settlement provides in the given resource
        '''
        total_prod = 0
        # for each adjacent hex to the settlement
        for adjacentHex in board.boardGraph[settlement].adjacentHexList:
            # get the resource type
            resourceType = board.hexTileDict[adjacentHex].resource.type

            # if the resource is the type we want to know about it
            if (resourceType == resource):
                # get the value on the hex
                numValue = board.hexTileDict[adjacentHex].resource.num

                # multiply production points by desire for that resuorce
                total_prod += self.diceRoll_expectation[numValue]

        return total_prod

        '''

        #Build road
        possibleRoads = board.get_setup_roads(self)


        # BUILDING ROAD

        randomEdge = np.random.randint(0, len(possibleRoads.keys()))
        self.build_road(list(possibleRoads.keys())[randomEdge][0], list(possibleRoads.keys())[randomEdge][1], board)
        '''

    def move(self, board):
        print("AI Player {} playing...".format(self.name))

        '''
        #Trade resources if there are excessive amounts of a particular resource
        self.trade()
        #Build a settlements, city and few roads
        possibleVertices = board.get_potential_settlements(self)
        if(possibleVertices != {} and (self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0 and self.resources['SHEEP'] > 0 and self.resources['WHEAT'] > 0)):
            randomVertex = np.random.randint(0, len(possibleVertices.keys()))
            self.build_settlement(list(possibleVertices.keys())[randomVertex], board)

        #Build a City
        possibleVertices = board.get_potential_cities(self)
        if(possibleVertices != {} and (self.resources['WHEAT'] >= 2 and self.resources['ORE'] >= 3)):
            randomVertex = np.random.randint(0, len(possibleVertices.keys()))
            self.build_city(list(possibleVertices.keys())[randomVertex], board)

        #Build a couple roads
        for i in range(2):
            if(self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0):
                possibleRoads = board.get_potential_roads(self)
                randomEdge = np.random.randint(0, len(possibleRoads.keys()))
                self.build_road(list(possibleRoads.keys())[randomEdge][0], list(possibleRoads.keys())[randomEdge][1], board)

        #Draw a Dev Card with 1/3 probability
        devCardNum = np.random.randint(0, 3)
        if(devCardNum == 0):
            self.draw_devCard(board)
        '''
        return

    # Wrapper function to control all trading
    def trade(self):
        '''
        for r1, r1_amount in self.resources.items():
            if(r1_amount >= 6): #heuristic to trade if a player has more than 5 of a particular resource
                for r2, r2_amount in self.resources.items():
                    if(r2_amount < 1):
                        self.trade_with_bank(r1, r2)
                        break
        '''

    # Choose which player to rob
    def choose_player_to_rob(self, board):
        '''Heuristic function to choose the player with maximum points.
        Choose hex with maximum other players, Avoid blocking own resource
        args: game board object
        returns: hex index and player to rob
        '''

        '''
        #Get list of robber spots
        robberHexDict = board.get_robber_spots()
        
        #Choose a hexTile with maximum adversary settlements
        maxHexScore = 0 #Keep only the best hex to rob
        for hex_ind, hexTile in robberHexDict.items():
            #Extract all 6 vertices of this hexTile
            vertexList = polygon_corners(board.flat, hexTile.hex)

            hexScore = 0 #Heuristic score for hexTile
            playerToRob_VP = 0
            playerToRob = None
            for vertex in vertexList:
                playerAtVertex = board.boardGraph[vertex].state['Player']
                if playerAtVertex == self:
                    hexScore -= self.victoryPoints
                elif playerAtVertex != None: #There is an adversary on this vertex
                    hexScore += playerAtVertex.visibleVictoryPoints
                    #Find strongest other player at this hex, provided player has resources
                    if playerAtVertex.visibleVictoryPoints >= playerToRob_VP and sum(playerAtVertex.resources.values()) > 0:
                        playerToRob_VP = playerAtVertex.visibleVictoryPoints
                        playerToRob = playerAtVertex
                else:
                    pass

            if hexScore >= maxHexScore and playerToRob != None:
                hexToRob_index = hex_ind
                playerToRob_hex = playerToRob
                maxHexScore = hexScore

        return hexToRob_index, playerToRob_hex
        '''

    def heuristic_move_robber(self, board):
        '''Function to control heuristic AI robber
        Calls the choose_player_to_rob and move_robber functions
        args: board object
        '''

        '''
        #Get the best hex and player to rob
        hex_i, playerRobbed = self.choose_player_to_rob(board)

        #Move the robber
        self.move_robber(hex_i, board, playerRobbed)
        '''

        return

    def heuristic_play_dev_card(self, board):
        '''Heuristic strategies to choose and play a dev card
        args: board object
        '''

        '''
        #Check if player can play a devCard this turn
        if self.devCardPlayedThisTurn != True:
            #Get a list of all the unique dev cards this player can play
            devCardsAvailable = []
            for cardName, cardAmount in self.devCards.items():
                if(cardName != 'VP' and cardAmount >= 1): #Exclude Victory points
                    devCardsAvailable.append((cardName, cardAmount))

            if(len(devCardsAvailable) >=1):
    #             If a hexTile is currently blocked, try and play a Knight

    #             If expansion needed, try road-builder

    #             If resources needed, try monopoly or year of plenty
        '''

    def resources_needed_for_settlement(self):
        '''Function to return the resources needed for a settlement
        args: player object - use self.resources
        returns: list of resources needed for a settlement
        '''
        resourcesNeededDict = {}
        for resourceName in self.resources.keys():
            if resourceName != 'ORE' and self.resources[resourceName] == 0:
                resourcesNeededDict[resourceName] = 1

        return resourcesNeededDict

    def resources_needed_for_city(self):
        '''Function to return the resources needed for a city
        args: player object - use self.resources
        returns: list of resources needed for a city
        '''
        resourcesNeededDict = {}
        if self.resources['ORE'] < 3:
            resourcesNeededDict['ORE'] = 3 - self.resources['ORE']

        if self.resources['WHEAT'] < 2:
            resourcesNeededDict['ORE'] = 2 - self.resources['WHEAT']

        return resourcesNeededDict

    def heuristic_discard(self):
        '''Function for the AI to choose a set of cards to discard upon rolling a 7
        '''
        return

    # Function to propose a trade -> give r1 and get r2
    # Propose a trade as a dictionary with {r1:amt_1, r2: amt_2} specifying the trade
    # def propose_trade_with_players(self):

    # Function to accept/reject trade - return True if accept
    # def accept_trade(self, r1_dict, r2_dict):

    # Function to find best action - based on gamestate

    def get_action(self):
        return

    # Function to execute the player's action
    def execute_action(self):
        return
