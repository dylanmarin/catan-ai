# Settlers of Catan
# Dylan AI class implementation

from board import *
from player import *
import numpy as np

# Class definition for an AI player


class dylanAIPlayer(player):

    # Update AI player flag and resources
    # DYLAN: Added params to give initial preference to different resources
    def updateAI(self, ore=4, brick=4, wheat=4, wood=4, sheep=4, port_desire=1, resource_diversity=0.65):
        self.isAI = True

        # Initialize resources with just correct number needed for set up (2 settlements and 2 road)
        # Dictionary that keeps track of resource amounts
        self.resources = {'ORE': 0, 'BRICK': 4,
                          'WHEAT': 2, 'WOOD': 4, 'SHEEP': 2}

        # DYLAN: Moved their diceRoll_expectation dict into a class var
        self.diceRoll_expectation = {2: 1, 3: 2, 4: 3, 5: 4,
                                     6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1, None: 0}

        '''
        # DYLAN: Added dicitonary of resource preferences to help tweak the ai on what to pick initially
        
        the relative size of these is what matters most, but I tried to keep them between 0-5, since they just 
        are used to scale the production points of desired reosurces


        '''
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

        '''
        resource diversity is a real value 0 to 1 that represents our desire for resource diversity

        0 means we do not care what resources we currently have when evaluating a settlement placement
        1 means that 5 production points of something we already have is proportionately bad to 5 production points of something we don't have at all

        '''
        self.resource_diversity = resource_diversity
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

        self.getDiversityOfSettlement(board, best_placement)

        self.evaluateSettlement(board, best_placement)
        self.build_settlement(best_placement, board)

    # DYLAN: Added evaluate settlement function
    def evaluateSettlement(self, board, settlement_location):
        '''
        multiply production by desire for that production

        add rating of ports usable by this our current settlements in addition to this 
        hypothetical settlement to the rating

        use self.resource_diversity to scale our desire for resource diversity

        '''

        debug = True

        total_rating = 0

        # Evaluate based on production points of surrounding hexes

        # for each resource type
        for resourceType in self.resourcePreferences.keys():
            # add the production points of that resource for this settlement to the rating

            production_points = self.getProductionPointsForSettlement(
                board, resourceType, settlement_location)

            total_rating += production_points * \
                self.resourcePreferences[resourceType]

            # if this settlement produces resourceType
            if production_points > 0:
                # then we subtract our current production for that resource, times our resource diversiity desire
                total_rating += self.resource_diversity * \
                    self.getDiversityOfSettlement(board, settlement_location)

        port = board.boardGraph[settlement_location].port
        if port:
            # multiply the addition by self.port_desire
            total_rating += self.port_desire * \
                self.evaluatePort(board, port, settlement_location)

        if debug:
            print("Rating of settlement: {}".format(total_rating))

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
                self.getOurProductionPoints(
                    board, port_resource_type, hypothetical_settlement)
        else:
            # if it is 3:1 add scaled down value proportional to total production points for all resources
            for resource_type in self.resources.keys():
                total_value += 0.33 * \
                    self.getOurProductionPoints(
                        board, resource_type, hypothetical_settlement)

        if debug:
            print("Eval for {} is {}".format(port, str(total_value)))

        return total_value

    def getOurProductionPoints(self, board, resource, hypothetical_settlement):
        # Return amount of hex of given resource times amount of ways to roll the number on each
        # hex for this specific player's settlements + an additional settlement

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

    def getDiversityOfSettlement(self, board, settlement_location):
        '''
        assign some diversity score to a given settlement. higher value means it has higher overall diversity

        we will divide the total number of adjacent hexes (max 3) by the amount of resources that are unique

        '''

        debug = True

        total_diversity_score = 0

        unique_resources_present = set()
        total_adjacent_hexes = 0

        # dict that tracks the max production of each resource that we've seen at this cell
        max_prod_for_type = {}
        for resource_type in self.resourcePreferences.keys():
            max_prod_for_type[resource_type] = self.getOurProductionPoints(
                board, resource_type, None)

        max_prod_for_type["DESERT"] = 0

        # for each adjacent resource
        for adjacentHex in board.boardGraph[settlement_location].adjacentHexList:
            resource_type = board.hexTileDict[adjacentHex].resource.type

            # add to the count of adjacent hexes and add the resource to the set of resources we've seen
            unique_resources_present.add(resource_type)
            total_adjacent_hexes += 1

            # get the production points of the current adjacent hex
            production_points = self.diceRoll_expectation[board.hexTileDict[adjacentHex].resource.num]

            # subtract the production points of the current resource at this hex by the amount of production we
            # already have for that resource. add the difference to our diversity score, with floor of 0
            total_diversity_score += max(production_points -
                                         max_prod_for_type[resource_type], 0)

            # if the current hex provides higher production than we had, use it in furhter calculations
            max_prod_for_type[resource_type] = max(
                production_points, max_prod_for_type[resource_type])

        if debug:
            print("{} out of {} hexes are unique types. Total new production points provided: {}".format(
                len(unique_resources_present), total_adjacent_hexes, total_diversity_score))

        total_diversity_score *= total_adjacent_hexes / \
            len(unique_resources_present)

        return total_diversity_score

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
