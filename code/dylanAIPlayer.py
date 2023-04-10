# Settlers of Catan
# Dylan AI class implementation

from board import *
from player import *
import numpy as np

# Class definition for an AI player


class dylanAIPlayer(player):

    # Update AI player flag and resources
    # DYLAN: Added params to give initial preference to different resources
    def updateAI(self, game, ore=4, brick=4, wheat=4, wood=4, sheep=4, port_desire=0.85, resource_diversity_desire=0.6):
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

        total = ore + brick + wheat + wood + sheep
        self.resourcePreferences = {
            'ORE': ore / total, 'BRICK': brick / total, 'WHEAT': wheat / total, 'WOOD': wood / total, 'SHEEP': sheep / total}

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
        self.resource_diversity_desire = resource_diversity_desire
        self.game = game

        print("Added new AI Player: ", self.name)

    # Function to build an initial settlement - just choose random spot for now

    def initial_setup(self, board):

        # get the best setup settlement placement according to our settlement evaluation
        best_placement = self.getBestSetupSettlement(board)

        print("testing place robber")
        self.place_robber(board)
        # self.getDiversityOfSettlement(board, best_placement)
        # self.evaluateSettlement(board, best_placement)
        self.build_settlement(best_placement, board)

        # 3 roads next to current
        best_road = self.pick_setup_road(board)
        self.build_road(best_road[0], best_road[1], board)


    # DYLAN: Added evaluate settlement function

    def getBestSetupSettlement(self, board):
        possible_placements = {}
        for placement in board.get_setup_settlements(self).keys():
            possible_placements[placement] = 0

        for p in possible_placements.keys():
            possible_placements[p] = self.evaluateSettlement(board, p)

        # get the placement with the max value
        return max(possible_placements, key=possible_placements.get)

    def evaluateSettlement(self, board, settlement_location):
        '''
        multiply production by desire for that production

        add rating of ports usable by this our current settlements in addition to this
        hypothetical settlement to the rating

        use self.resource_diversity_desire to scale our desire for resource diversity

        '''

        debug = False

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
                # then we add a diversity score multiplied by how much we car about resource diversity
                total_rating += self.resource_diversity_desire * \
                    self.getDiversityOfSettlement(board, settlement_location)

        port = board.boardGraph[settlement_location].port
        if port:
            # multiply the addition by self.port_desire
            total_rating += self.port_desire * \
                self.evaluatePort(board, port, settlement_location)

        total_rating += self.resource_synergy_in_setup(
            board, settlement_location)

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

        we will divide the total number of adjacent hexes(max 3) by the amount of resources that are unique

        '''

        debug = False

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

    def resource_synergy_in_setup(self, board, settlement_location):
        '''
        This is a function that is meant to provide a rating for a given settlement based
        on how well the resources that the settlement provides synergize with each other
        and with our current production.

        Combination of self_synergy and setup_synergy

        self_synergy benefits settlements that work well on their own,
        i.e. an ORE-WHEAT-SHEEP settlement, or a WOOD-BRICK settlement

        setup_synergy increases when the production points that the settlement provides
        help us balance out ratios for building things
        '''
        debug = False

        total_score = 0
        settlement_resources = board.boardGraph[settlement_location].adjacentHexList
        settlement_production_points = {}

        for resource in self.resourcePreferences:
            settlement_production_points[resource] = self.getProductionPointsForSettlement(
                board, resource, settlement_location)

        # benefit wood-brick, wheat-ore, ore-wheat-sheep
        self_synergy = 0

        if "WOOD" in settlement_resources and "BRICK" in settlement_resources:

            self_synergy += settlement_production_points["WOOD"]
            self_synergy += settlement_production_points["BRICK"]

            self_synergy *= (self.resourcePreferences["WOOD"] +
                             self.resourcePreferences["BRICK"])

            if debug:
                print("Benefiting WOOD-BRICK by {}".format(self_synergy))

        elif "ORE" in settlement_resources and "WHEAT" in settlement_resources and "SHEEP" in settlement_resources:
            self_synergy += settlement_production_points["ORE"]
            self_synergy += settlement_production_points["WHEAT"]
            self_synergy += settlement_production_points["SHEEP"]

            self_synergy *= (self.resourcePreferences["ORE"] +
                             self.resourcePreferences["WHEAT"] + self.resourcePreferences["SHEEP"])
            if debug:
                print("Benefiting ORE-WHEAT-SHEEP by {}".format(self_synergy))

        elif "WHEAT" in settlement_resources and "SHEEP" in settlement_resources:
            self_synergy += settlement_production_points["WHEAT"]
            self_synergy += settlement_production_points["SHEEP"]

            self_synergy *= (self.resourcePreferences["WHEAT"] +
                             self.resourcePreferences["SHEEP"])
            if debug:
                print("Benefiting WHEAT-SHEEP by {}".format(self_synergy))

        return self_synergy

        our_production_points = {}

        for resource in self.resourcePreferences:
            our_production_points[resource] = self.getOurProductionPoints(
                board, resource, None)

        # for resource in settlement_resources:

        '''
        in general we are using ratio of buyable items as guidelines for synergy.
        # however, we dont wanna benefit surpassing the ratio, as in, if the settlement tips
        # our ore ratio to be too high, we dont want to punish
        '''

        '''
        if this settlement has wood or brick, we care if it balances out our wood/brick to be closer to our resource preferences
        or if it balances out wood-brick-sheep-wheat to be like 3-3-2-2 ish
        '''
        if "WOOD" in settlement_resources:
            old_wood_brick_ratio = our_production_points["WOOD"] / \
                our_production_points["BRICK"]
            new_wood_brick_ratio = (our_production_points["WOOD"] + settlement_production_points["WOOD"]) / \
                (our_production_points["BRICK"] +
                    settlement_production_points["BRICK"])

            # first term is negative if we had more brick than wood
            # second term is negative if we had more brick than wood

            somethingsomething = (old_wood_brick_ratio - 0.5) - \
                (new_wood_brick_ratio - 0.5)

            return
        if resource == "BRICK":
            return

        '''
        if this settlement has sheep, we want to benefit it for making our ore-wheat-sheep ratio 1-1-1
        or for making our wood-brick-sheep-wheat to be like 3-3-2-2 ish
        '''

        '''
        if this settlement has wheat, we want to benefit it for making our ore-wheat-sheep ratio 1-1-1
        or for making our wood-brick-sheep-wheat to be like 3-3-2-2 ish

        OR for making our wheat-ore ratio more 2: 3
        '''

        '''
        if this settlement has ore, we want to benefit it for making our ore-wheat-sheep ratio 1-1-1
        or for making our wheat-ore ratio more 2: 3
        '''

        total_score += self_synergy

        return total_score

    def pick_setup_road(self, board):
        '''
        Function used just for initial road choice
        '''

        # get next best settlement, and build a road in the direction of it
        last_settlement = self.buildGraph['SETTLEMENTS'][-1]

        possible_placements = {}
        for placement in board.get_setup_settlements(self).keys():
            if placement != last_settlement:
                possible_placements[placement] = 0

        for p in possible_placements.keys():
            possible_placements[p] = self.evaluateSettlement(board, p)

        # get the next best settlement spot and build in its direction
        dest = max(possible_placements, key=possible_placements.get)

        left = (dest.x - last_settlement.x) < 0
        right = (dest.x - last_settlement.x) > 0
        up = (dest.y - last_settlement.y) < 0
        down = (dest.y - last_settlement.y) > 0

        # gets 3 roads for last settlement was placed
        possible_roads = board.get_setup_roads(self)

        valid_options = {}

        for road in possible_roads:
            valid_options[road] = 0
            start = road[0]
            end = road[1]

            if (end.x - start.x < 0) and left:
                valid_options[road] += 1

            if (end.x - start.x > 0) and right:
                valid_options[road] += 1

            if (end.y - start.y < 0) and up:
                valid_options[road] += 1

            if (end.y - start.y > 0) and down:
                valid_options[road] += 1

        return max(valid_options, key=valid_options.get)

    def move(self, board):
        print("AI Player {} playing...".format(self.name))
        '''
        Options: 

        road
        settlement
        city
        buy a dev card
        play a dev card
        propose a trade
            - to players
            - with port or bank

        possible flow:

        resources blocked OR it will give us largest army OR put us ahead in a current tie of knights:
            play knight

        roll

        discard cards if necessary
        move robber if necessary

        check which (building) options are possible:
            road
            settlement
            city
            dev

        get utility for all options:
            settlement and city can both use settlement evaluate
            road utility probs has something to do with settlements it opens up
            buying dev card "utility" probably wins out when our production aligns with dev cards, and when we cant do other options

        for each possible option, in order of their utility:
            if we can do it, do it
            if we can't, see if we have a dev card that helps us
                if we do, play it and try to do our option again

            if we can't do it, and we have no useful dev card:
                see if porting or trading with bank allows us to do it

        '''

        # we may have already played a knight before rolling

        # (takes into account if we have already played a knight)
        if self.should_play_knight_after_rolling(board):
            # NOTE: does not take into account whether waiting to play another dev card is better
            self.place_robber(board)




        '''
        # Trade resources if there are excessive amounts of a particular resource
        self.trade()
        # Build a settlements, city and few roads
        possibleVertices = board.get_potential_settlements(self)
        if(possibleVertices != {} and (self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0 and self.resources['SHEEP'] > 0 and self.resources['WHEAT'] > 0)):
            randomVertex = np.random.randint(0, len(possibleVertices.keys()))
            self.build_settlement(list(possibleVertices.keys())[randomVertex], board)

        # Build a City
        possibleVertices = board.get_potential_cities(self)
        if(possibleVertices != {} and (self.resources['WHEAT'] >= 2 and self.resources['ORE'] >= 3)):
            randomVertex = np.random.randint(0, len(possibleVertices.keys()))
            self.build_city(list(possibleVertices.keys())[randomVertex], board)

        # Build a couple roads
        for i in range(2):
            if(self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0):
                possibleRoads = board.get_potential_roads(self)
                randomEdge = np.random.randint(0, len(possibleRoads.keys()))
                self.build_road(list(possibleRoads.keys())[randomEdge][0], list(possibleRoads.keys())[randomEdge][1], board)

        # Draw a Dev Card with 1/3 probability
        devCardNum = np.random.randint(0, 3)
        if(devCardNum == 0):
            self.draw_devCard(board)
        '''
        return

    def should_play_knight_before_rolling(self, board):
        # NOTE: Doesn't take into account value of staying blocked but playing a different dev card later in the turn

        # if we are blocked
        if self.any_settlement_blocked_by_robber(board):
            # if we have exactly 7 cards, then we should usually be fine to play the knight, but
            # sometimes if we play the knight we will get 8 cards and then roll a 7 and have to
            # discard, so we should only do it most of the time
            if sum(self.resources.values()) == 7:
                # return true 5/6 times
                return np.random.randint(0, 36) >= 6
            else:
                # play knight
                return True
        return False

    def should_play_knight_after_rolling(self, board):
        '''
        if we are blocked, play it for future resource rolls until our next turn

        if it will give us largest army for the win, play it

        if we are tied in amount of knights played, and opponent has any dev cards, play it
            if they don't have dev cards, we can wait
        '''
        if self.devCardPlayedThisTurn:
            return False
        
        # shouldn't if we cant
        if self.devCards["KNIGHT"] == 0:
            return False
            

        if self.any_settlement_blocked_by_robber(board):
            return True

        # if anyone has more knights than us
        for p in list(self.game.playerQueue.queue):
            # NOTE: doesn't take into account if we should ever give up and not play the knight
            if (p.knightsPlayed > self.knightsPlayed):
                return True

        play_flag = True
        # if we don't have largest army but would win if we played a knight
        if self.victoryPoints >= self.max_points - 2 and not self.largestArmyFlag:
            # if we have already played at least 2 knights
            if self.knightsPlayed >= 2:
                # and every other player has AT MOST the same amount of knights:
                for p in list(self.game.playerQueue.queue):
                    # if any other player has strictly more knights than us, we wont take largest army
                    if (p.knightsPlayed > self.knightsPlayed):
                        play_flag = False

        # if it would give us largest army for the win, play it
        if play_flag:
            return True

        # if we are tied with anyone in number of knights who has a dev card, play a knight
        for p in list(self.game.playerQueue.queue):
            if (p.knightsPlayed == self.knightsPlayed) and (sum(p.devCards.values()) >= 1):
                return True

        return False

    def place_robber(self, board):
        # potentialRobberDict = self.board.get_robber_spots() # excludes the spot that had the orbber on it

        all_players = list(self.game.playerQueue.queue)

        # in order of number of victory points 
        # NOTE: AI is currently cheating by knowing whether people have hidden VP dev cards
        all_players.sort(reverse=True, key=lambda p: p.victoryPoints)


        # check if all opponents have 0 cards
        all_have_zero = True
        for player in all_players:
            # skip ourselves
            if player != self:

                if sum(player.resources.values()) > 0:
                    all_have_zero = False
    

        # for each opponents with at least one card (or if all opponents have 0 cards then all of them)
        for player in all_players:
            # skip ourselves
            if player != self:
                # if this player has cards, or if everyone has zero cards
                if sum(player.resources.values() > 0) or all_have_zero:
                    settlements = player.buildGraph["SETTLEMENTS"]

                    # rate all opponent settlements and sort them
                    settlements.sort(reverse=True, key=lambda s : player.evaluateSettlement(board, s))

                    # for each settlement
                    for settlement in settlements:

                        


                        # get all adjacent hexes and sort them in order of production points
                        for adj_hex in board.boardGraph[settlement].adjacentHexList:
                            # if the hex is adjacent to our settlement, skip it
                            if not self.hex_is_adjacent_to_us(board, hex):
                                # otherwise place on the hex with most production   





                    

        # TODO: failsafe if somehow it all is not possible

        self.devCardPlayedThisTurn = True
        return

    def any_settlement_blocked_by_robber(self, board):
        for settlement in self.buildGraph["SETTLEMENTS"]:
            for adj_hex in board.boardGraph[settlement].adjacentHexList:
                if (board.hexTileDict[adj_hex].robber == True):
                    return True
        return False

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
        # Get list of robber spots
        robberHexDict = board.get_robber_spots()
        
        # Choose a hexTile with maximum adversary settlements
        maxHexScore = 0 #Keep only the best hex to rob
        for hex_ind, hexTile in robberHexDict.items():
            # Extract all 6 vertices of this hexTile
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
                    # Find strongest other player at this hex, provided player has resources
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
        # Get the best hex and player to rob
        hex_i, playerRobbed = self.choose_player_to_rob(board)

        # Move the robber
        self.move_robber(hex_i, board, playerRobbed)
        '''

        return

    def heuristic_play_dev_card(self, board):
        '''Heuristic strategies to choose and play a dev card
        args: board object
        '''

        '''
        # Check if player can play a devCard this turn
        if self.devCardPlayedThisTurn != True:
            # Get a list of all the unique dev cards this player can play
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
