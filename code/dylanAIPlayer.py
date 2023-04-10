# Settlers of Catan
# Dylan AI class implementation

from board import *
from player import *
import numpy as np
import copy

# Class definition for an AI player


class dylanAIPlayer(player):

    # Update AI player flag and resources
    # DYLAN: Added params to give initial preference to different resources
    def updateAI(self, game, ore=4, brick=4, wheat=4, wood=4, sheep=4, port_desire=50.85, resource_diversity_desire=0.6):
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

    def evaluateOpponentSettlement(self, board, settlement_location):
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
        # may have rolled a 7 and moved the robber AND discarded cards

        # (takes into account if we have already played a knight)
        if self.should_play_knight_after_rolling(board):
            # NOTE: does not take into account whether waiting to play another dev card is better
            self.place_robber(board)

        moves_made = 0

        able_to_do_something = True
        while able_to_do_something:
            # while we are aeble to do something
            goals = self.get_move_goals().keys()
            goals.sort(
                reverse=True, key=lambda goal: self.get_move_goals()[goal])

            for option in goals:

                if self.able_to_do(option):
                    # TODO: do it
                    self.make_move(option)

                    # anytime we do an option, we do it and go back to top of loop
                    moves_made += 1
                    able_to_do_something = True
                    break
                elif self.able_to_trade_for(option):
                    # TODO:
                    self.make_said_trades()

                    # do it
                    self.make_move(option)

                    # anytime we do an option, we do it and go back to top of loop
                    moves_made += 1
                    able_to_do_something = True
                    break

                else:
                    # if we have gone through all options without doing anything, we don't need to loop again
                    able_to_do_something = False

        if moves_made == 0:
            # try trading with players?? maybe? and then try making moves again
            return

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

    def get_move_goals(self):
        '''
        This function will assign a "desire" rating for each of the 5 options. It does not take into account whether they are possible or not.
        '''
        goals = {"ROAD": 0, "SETTLEMENT": 0,
                 "CITY": 0, "BUY_DEV": 0, "PLAY_DEV": 0}

        goals["ROAD"] = self.get_road_desire()
        goals["SETTLEMENT"] = self.get_settlement_desire()
        goals["CITY"] = self.get_city_desire()
        goals["BUY_DEV"] = self.get_buy_dev_desire()
        goals["PLAY_DEV"] = self.get_play_dev_desire()

        return goals

    def able_to_do(self, option):
        if option == "ROAD":
            return self.can_buy_road()
        elif option == "SETTLEMENT":
            return self.can_buy_settlement()
        elif option == "CITY":
            return self.can_buy_city()
        elif option == "BUY_DEV":
            return self.can_buy_dev_card()
        elif option == "PLAY_DEV":
            #shouldnt be reached
            return True


    def able_to_trade_for(self, option):
        #TODO
        #TODO
        #TODO
        #TODO
        #TODO
        #TODO
        if option == "ROAD":
            return self.can_get_resources_through_trading({})
        elif option == "SETTLEMENT":
            return self.can_get_resources_through_trading({})
        elif option == "CITY":
            return self.can_get_resources_through_trading({})
        elif option == "BUY_DEV":
            return self.can_get_resources_through_trading({})
        elif option == "PLAY_DEV":
            #shouldnt be reached
            return True


            


    '''
    "desire"/utility functions. main goals for these is that they do the best thing when it is obvious. DONT BE STUPID!
    '''

    def get_road_desire(self):
        '''
        roads are desired if we have 0 possible settlement spots.

        roads are desired if we are tied for longest road

        roads are desired if we dont have longest road and it would give us the win

        roads are desired 
        '''
        utility = 0

        return utility

    def get_settlement_desire(self):
        '''
        we dont care to settle if we have no spots. (we do want to settle even if we dont have resources, though)

        a settlement is approximately as valuable as the production it provides. use evaluate function on settlements that we could possibly build

        we max out utility if we are 1 VP from winning
        '''
        utility = 0

        return utility

    def get_city_desire(self):
        '''
        a city is as useful as the production it provides. we can evaluate it as if it was another settlement in the same spot as an existing one

        we max out utility if we are 1 VP from winning
        '''
        utility = 0

        return utility

    def get_buy_dev_desire(self):
        '''
        dev card should be somewhere in the middle. we kind of want to buy dev cards only if our production matches it well, 
        but we dont want to buy dev cards if it will ruin our other stuff
        '''
        utility = 0

        return utility

    def get_play_dev_desire(self):
        '''

        dont have to account for knights because they would've been played sooner

        road building is good if we currently want to build roads

        monopoly is good if we think/know there are a lot of cards out there. it is even better if we have a relevant port

        year of plenty is good if we need 2 cards for our favorite action

        overall utility = max of those 3 ratings
        '''
        utility = 0

        return utility

    '''
    helper functions to tell us if we can do something
    '''

    def can_buy_road(self):
        return self.resources["BRICK"] > 0 and self.resources["WOOD"] > 0

    def can_buy_settlement(self):
        return self.resources["BRICK"] > 0 and self.resources["WOOD"] > 0 and self.resources["SHEEP"] > 0 and self.resources["WHEAT"] > 0

    def can_buy_city(self):
        return self.resources["WHEAT"] >= 2 and self.resources["ORE"] >= 3

    def can_buy_dev_card(self):
        return self.resources["ORE"] > 0 and self.resources["SHEEP"] > 0 and self.resources["WHEAT"] > 0

    def can_play_dev_card(self):
        return sum(self.devCards.values()) > 0 and not self.devCardPlayedThisTurn

    def can_get_resources_through_trading(self, desired_resources):
        '''
        desired resources is a dict from resource string to amount desired

        function checks if through 4:1, 3:1, 2:1 trading it can reach the desired resources
        '''

        debug = True

        theoretical_resources = copy.deepcopy(self.resources)

        # for each resource
        for resource in desired_resources.keys():
            theoretical_resources[resource] -= desired_resources[resource]

        # while we can't pay for it
        while not all(theoretical_resources[resource] >= 0 for resource in theoretical_resources):
            if debug:
                print(theoretical_resources)

            has_traded = False

            # try all ports
            for port in self.portList:

                # if we have a 2:1 port
                if port[:3] == "2:1":
                    port_resource_type = port[4:]
                    if debug:
                        print("Checking 2:1 {} options...".format(
                            port_resource_type))

                    # if we have 2 of the item
                    if theoretical_resources[port_resource_type] >= 2:

                        # hypothetically make the trade
                        theoretical_resources[port_resource_type] -= 2

                        for resource in theoretical_resources:
                            if theoretical_resources[resource] < 0:
                                theoretical_resources[resource] += 1

                                # only do it once
                                has_traded = True
                                break

                        # break to top of while loop if we did make a trade
                        break

                if port[:3] == "3:1":
                    if debug:
                        print("Checking 3:1 options...")
                    # go through each resource
                    for trade_resource in theoretical_resources:

                        # if we have 3 of the item
                        if theoretical_resources[trade_resource] >= 3:

                            # hypothetically make the trade
                            theoretical_resources[trade_resource] -= 3

                            # add it to whatever we still need
                            for resource in theoretical_resources:
                                if theoretical_resources[resource] < 0:
                                    theoretical_resources[resource] += 1

                                    # only do it once
                                    has_traded = True
                                    break

                            # break to top of while loop if we did make a theoretical trade
                            break

            if has_traded:
                continue

            # no port, so try 4:1

            # go through each resource
            for trade_resource in theoretical_resources:
                if debug:
                    print("Checking 4:1 for {} options...".format(trade_resource))

                # if we have 4 of the item
                if theoretical_resources[trade_resource] >= 4:

                    # hypothetically make the trade
                    theoretical_resources[trade_resource] -= 4

                    # add it to whatever we still need
                    for resource in theoretical_resources:
                        if theoretical_resources[resource] < 0:
                            theoretical_resources[resource] += 1

                            # only do it once
                            has_traded = True
                            break

                    # break to top of while loop if we did make a trade
                    break

            if has_traded:
                continue

            # if we ever go through the loop and don't make a trade, we reach here and therefore cannot do it
            return False

        return True

    def should_play_knight_before_rolling(self, board):
        # NOTE: Doesn't take into account value of staying blocked but playing a different dev card later in the turn

        if self.devCards["KNIGHT"] == 0:
            return False

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
        print("{} is moving the robber...".format(self.name))

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

        valid_robber_spots = board.get_robber_spots()

        # for each opponents with at least one card (or if all opponents have 0 cards then all of them)
        for player in all_players:
            # skip ourselves
            if player != self:
                # if this player has cards, or if everyone has zero cards
                if sum(player.resources.values()) > 0 or all_have_zero:
                    settlements = player.buildGraph["SETTLEMENTS"]

                    # rate all opponent settlements and sort them
                    # TODO
                    # TODO
                    # TODO
                    # TODO
                    # TODO: evaluate opponent settlement
                    # settlements.sort(
                    #     reverse=True, key=lambda s: player.evaluateSettlement(board, s))

                    # for each settlement
                    for settlement in settlements:
                        valid_hex_options = []

                        # get all adjacent hexes and sort them in order of production points
                        for adj_hex in board.boardGraph[settlement].adjacentHexList:

                            # if the hex is adjacent to our settlement, skip it
                            if not self.hex_is_adjacent_to_us(board, adj_hex) and adj_hex in valid_robber_spots:
                                # otherwise place on the hex with most production
                                valid_hex_options.append(adj_hex)

                        valid_hex_options.sort(
                            reverse=True, key=lambda h: self.production_points_for_hex(board, h))

                        for option in valid_hex_options:
                            self.move_robber(option, board, player)
                            self.devCardPlayedThisTurn = True
                            return

        # TODO: failsafe if somehow it all is not possible, just pick one that has most production next to someone with a card
        return

    def production_points_for_hex(self, board, hex_num):
        return self.diceRoll_expectation[board.hexTileDict[hex_num].resource.num]

    def hex_is_adjacent_to_us(self, board, adjacent_hex):
        for settlement in self.buildGraph["SETTLEMENTS"]:
            for adj_hex in board.boardGraph[settlement].adjacentHexList:
                if adj_hex == adjacent_hex:
                    return True

        return False

    def any_settlement_blocked_by_robber(self, board):
        for settlement in self.buildGraph["SETTLEMENTS"]:
            for adj_hex in board.boardGraph[settlement].adjacentHexList:
                if (board.hexTileDict[adj_hex].robber == True):
                    return True
        return False

    # Wrapper func
    def discard_cards(self):
        '''
        Function for the AI to choose a set of cards to discard upon rolling a 7
        '''

        # TODO

        return

    # Function to propose a trade -> give r1 and get r2
    # Propose a trade as a dictionary with {r1:amt_1, r2: amt_2} specifying the trade
    # def propose_trade_with_players(self):

    # Function to accept/reject trade - return True if accept
    # def accept_trade(self, r1_dict, r2_dict):
