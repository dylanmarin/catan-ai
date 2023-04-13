# Settlers of Catan
# Dylan AI class implementation

from board import *
from player import *
import numpy as np
import copy
import time

# Class definition for an AI player


class dylanAIPlayer(player):

    # Update AI player flag and resources
    # DYLAN: Added params to give initial preference to different resources
    def updateAI(self, game, ore=4, brick=2, wheat=4, wood=2, sheep=2, port_desire=0.85, resource_diversity_desire=0.6):
        self.isAI = True

        # Initialize resources with just correct number needed for set up (2 settlements and 2 road)
        # Dictionary that keeps track of resource amounts
        self.resources = {'ORE': 0, 'BRICK': 4,
                          'WHEAT': 2, 'WOOD': 4, 'SHEEP': 2}
        # self.resources = {'ORE': 2, 'BRICK': 100,
        #                   'WHEAT': 4, 'WOOD': 100, 'SHEEP': 4}

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

        self.road_cost = {'ORE': 0, 'BRICK': 1,
                          'WHEAT': 0, 'WOOD': 1, 'SHEEP': 0}
        self.city_cost = {'ORE': 3, 'BRICK': 0,
                          'WHEAT': 2, 'WOOD': 0, 'SHEEP': 0}
        self.settlement_cost = {'ORE': 0, 'BRICK': 1,
                                'WHEAT': 1, 'WOOD': 1, 'SHEEP': 1}
        self.buy_dev_cost = {'ORE': 1, 'BRICK': 0,
                             'WHEAT': 1, 'WOOD': 0, 'SHEEP': 1}
        self.play_dev_cost = {'ORE': 0, 'BRICK': 0,
                              'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}

        self.road_resources = ['WOOD', 'BRICK']
        self.city_resources = ['ORE', 'WHEAT']
        self.settlement_resources = ['WOOD', 'BRICK', 'WHEAT', 'SHEEP']
        self.buy_dev_resources = ['ORE', 'WHEAT', 'SHEEP']

        self.option_to_resources_required_dict = \
            {"BUY_DEV": self.buy_dev_cost,
             "SETTLEMENT": self.settlement_cost,
             "CITY": self.city_cost,
             "ROAD": self.road_cost,
             "PLAY_DEV": self.play_dev_cost}

        self.game = game

        print("Added new AI Player: ", self.name)

    # Function to build an initial settlement - just choose random spot for now

    def initial_setup(self, board):

        # get the best setup settlement placement according to our settlement evaluation
        best_placement = self.get_best_setup_settlement(board)

        # self.getDiversityOfSettlement(board, best_placement)
        # self.evaluateSettlement(board, best_placement)
        self.build_settlement(best_placement, board)

        # 3 roads next to current
        # best_road = self.pick_setup_road(board)
        # self.build_road(best_road[0], best_road[1], board)

        self.place_best_road(board, setup=True)

    # DYLAN: Added evaluate settlement function

    def get_best_setup_settlement(self, board, exclude=[]):
        possible_placements = {}
        for placement in board.get_setup_settlements(self).keys():
            # if we want to exclude it, dont add it
            if placement not in exclude:
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

        # if we already have the port, it doesn't provide additional value
        if port in self.portList:
            return total_value

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

        TODO
        TODO
        TODO
        TODO
        TODO

        first: use this function in initial setup again

        then: make it estimate the next best settlement that it would actually be able to build at (given position in choosing), and point there
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
        print("{}'s TURN...".format(self.name))
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
        debug = True
        # we may have already played a knight before rolling
        # may have rolled a 7 and moved the robber AND discarded cards

        # (takes into account if we have already played a knight)
        if self.should_play_knight_after_rolling(board):
            # NOTE: does not take into account whether waiting to play another dev card is better
            self.play_knight(board)

        moves_made = 0

        able_to_do_something = True
        while able_to_do_something:
            able_to_do_something = False
            # while we are able to do something
            move_goals = self.get_move_goals(board)

            options = list(move_goals.keys())
            options.sort(
                reverse=True, key=lambda goal: move_goals[goal])

            for option in options:

                if debug:
                    print("{} desire: {}".format(option, move_goals[option]))

                if move_goals[option] == 0:
                    continue

                if self.able_to_do(option):
                    if debug:
                        print("Able to: {}".format(option))

                    self.make_move(board, option)

                    # anytime we do an option, we do it and go back to top of loop
                    moves_made += 1
                    able_to_do_something = True
                    break
                elif self.able_to_trade_for(option):
                    if debug:
                        print("Able to: {}".format(option))
                    # make the trades
                    self.make_trades_for(option)

                    # do it
                    self.make_move(board, option)

                    # anytime we do an option, we do it and go back to top of loop
                    moves_made += 1
                    able_to_do_something = True
                    break
                else:
                    # if we have < 7 cards, discard lower rated options that will hinder our current goal
                    if sum(self.resources.values()) <= 7:
                        goals_to_remove = self.remove_conflicting_goals(
                            option, options)
                        for goal_to_remove in goals_to_remove:
                            if goal_to_remove in options:
                                options.remove(goal_to_remove)

                    # while we 7+ cards, trade towards our highest rated option
                    while sum(self.resources.values()) > 7:
                        if debug:
                            print("{} has {} cards, so it will attempt to trade for {}".format(
                                self.name, sum(self.resources.values()), option))
                        # if we have 7 or more cards, first try porting for a resource that will help us towards our goal.
                        if self.make_one_trade_for_option(option):
                            # if we were able to make any trade:
                            # don't do a lower rated option if it will make it impossible to do a higher rated option:
                            # i.e. dont build a road if we'd prefer to build a settlement
                            # unless we currently have lots of cards, then spending is prioritized
                            goals_to_remove = self.remove_conflicting_goals(
                                option, options)
                            for goal_to_remove in goals_to_remove:
                                if goal_to_remove in options:
                                    options.remove(goal_to_remove)
                        else:

                            if debug:
                                print("{} was unable to trade for {} and still has {} cards".format(
                                    self.name, option, sum(self.resources.values())))
                            # if we couldn't trade for something, then we can keep lower rated options in the queue
                            break

                    # if debug:
                    #     print("Not able to do top choice")

                    # if we have gone through all options without doing anything, we don't need to loop again
                    # TODO: propose trade should propose one trade and return true if accepted
                    # able_to_do_something = self.propose_trade()
                    continue
        return

    def remove_conflicting_goals(self, current_goal, all_options):
        '''
        given the current goal, return any option that would disallow us to build the current goal
        '''
        debug = False
        goals_to_remove = []

        for option in all_options:
            if option != current_goal or option == "PLAY_DEV":
                if debug:
                    print("Checking if {} conflicts with {}".format(
                        option, current_goal))
                if not self.can_build_without_breaking(current_goal, option):
                    if debug:
                        print("It did conflict")
                    goals_to_remove.append(option)

                else:
                    if debug:
                        print("It did not conflict")

        if debug:
            print()

        return goals_to_remove

    def can_build_without_breaking(self, build_option, breaking_option):
        '''
        given two options, determine whether we have enough resources to do the breaking option without going below what is needed for the build option

        return true if we can build our breaking option and we have not gone below what cards are needed for the build option
        '''
        # doesnt cost anything
        if breaking_option == "PLAY_DEV":
            return True
        
        debug = False and build_option == "SETTLEMENT"

        # dict from option to a DICT OF RESOURCE:NUMBER representing the cost for the option
        cost_of_build_option = self.option_to_resources_required_dict[build_option]

        # dict from option to a DICT OF RESOURCE:NUMBER representing the cost for the option
        cost_of_breaking_option = self.option_to_resources_required_dict[breaking_option]

        if debug:
            print("Checking if {} conflicts with {}".format(
                breaking_option, build_option))

        # for each resource
        for resource in cost_of_build_option.keys():

            current_amount = self.resources[resource]
            required_amount = cost_of_build_option[resource]
            possible_breaking_amount = cost_of_breaking_option[resource]


            # if we don't need this resource for either of the build options, it doesnt matter
            # if we dont have the resource, then building anything cant decrease this below the threshold
            if required_amount == 0 or possible_breaking_amount == 0 or current_amount == 0:
                if debug:
                    print(" It does not conflict")
                continue

            if debug:
                print(" For {}, we have {} {}, we need {}, and want {} for {}".format(
                    build_option, current_amount, resource, required_amount, possible_breaking_amount, breaking_option))
                print(" If we built {}, we'd have {} remaining for {}".format(breaking_option, current_amount-possible_breaking_amount, build_option))

            # if our current amount minus the cost of the breaking option is less than what we need for our
            # build option, it would break our resources for the build optoin
            if current_amount - possible_breaking_amount < required_amount:
                if debug:
                    print(" It DOES conflict")
                return False


            if debug:
                print()
        return True

    def make_one_trade_for_option(self, option):
        '''
        attempts to make any trade towards the chosen option. if any trade is made, returns True.
        otherwise, False
        '''
        if option == "ROAD":
            return self.trade_for_resources({'ORE': 0, 'BRICK': 1,
                                             'WHEAT': 0, 'WOOD': 1, 'SHEEP': 0}, just_one=True)
        elif option == "SETTLEMENT":
            return self.trade_for_resources({'ORE': 0, 'BRICK': 1,
                                             'WHEAT': 1, 'WOOD': 1, 'SHEEP': 1}, just_one=True)
        elif option == "CITY":
            return self.trade_for_resources({'ORE': 3, 'BRICK': 0,
                                             'WHEAT': 2, 'WOOD': 0, 'SHEEP': 0}, just_one=True)
        elif option == "BUY_DEV":
            return self.trade_for_resources({'ORE': 1, 'BRICK': 0,
                                             'WHEAT': 1, 'WOOD': 0, 'SHEEP': 1}, just_one=True)
        elif option == "PLAY_DEV":
            # should not be reached
            return False

        return False

    def get_move_goals(self, board):
        '''
        This function will assign a "desire" rating for each of the 5 options. It does not take into account whether they are possible or not.
        '''
        debug = False
        goals = {"ROAD": 0, "SETTLEMENT": 0,
                 "CITY": 0, "BUY_DEV": 0, "PLAY_DEV": 0}

        goals["ROAD"] = self.get_road_desire(board)
        goals["SETTLEMENT"] = self.get_settlement_desire(board)
        goals["CITY"] = self.get_city_desire(board)
        goals["BUY_DEV"] = self.get_buy_dev_desire(board)
        goals["PLAY_DEV"] = self.get_play_dev_desire(board)

        if debug:
            for item in goals.keys():
                print("{} desire: {}".format(item, goals[item]))
            print()

        return goals

    def make_move(self, board, option):
        '''
        helper function given an option, plays the AI's chosen move for that option. assumes it is possible.
        '''
        if option == "ROAD":
            self.place_best_road(board)
            return
        elif option == "SETTLEMENT":
            self.place_best_settlement(board)
            return
        elif option == "CITY":
            self.place_best_city(board)
            return
        elif option == "BUY_DEV":
            self.draw_devCard(board)
            return
        elif option == "PLAY_DEV":
            self.play_best_dev_card(board)
            return

    def place_best_road(self, board, setup=False):
        '''
        two main ways to place road:
            - place to reach a new settlement spot
            - place to get longest road
        '''

        possible_roads = board.get_potential_roads(self)

        if setup:
            possible_roads = board.get_setup_roads(self)

        best_road = max(possible_roads, key=lambda road: self.evaluateRoad(
            board, road, setup=setup))

        self.build_road(best_road[0], best_road[1], board)
        return

    def evaluateRoad(self, board, road, debug=False, setup=False):
        '''
        function to evaluate roads


        if it gives us longest road, apply some utility
            if it would give us longest road for the win, apply MAX utility

        if it is within 2 roads of giving us largest road, apply 1/2 the amount

        if it allows us to settle at a spot, add some utility times/plus the amount of value of the settlement

        if it allows us to build another road that will allow us to settle, do half of the utility times/plus max value of the settlement

        if it is the first of 3 roads towards a settlement, do the above but with 1/3

        if it increases max road length, apply medium amount of utility, close to that of allowing us to settle, but without settlement multiplier

        IMPROVEMNET: cutting off opponents        
        '''

        utility = 0
        longest_road_utility = 50.0
        settlement_base_utility = 5.0
        increase_max_length_utility = 25.0

        if setup:
            increase_max_length_utility = 0
            longest_road_utility = 0

        # new roads that we can build given the current road
        one_degree_roads = self.get_potential_roads_with(board, [road])

        two_degree_roads = self.get_potential_roads_with(
            board, one_degree_roads)

        # if we can even take longest road
        if self.can_take_longest_road():
            # if this road would do it
            if self.would_give_us_longest(board, [road]):
                utility += longest_road_utility

                if debug:
                    print("Road gives us longest road. Utility {}".format(utility))
                # if it gives us the win, just max it out
                if self.max_points - self.victoryPoints <= 2:
                    utility += 1000

                    if debug:
                        print(
                            "Longest Road would give us the win. Utility {}".format(utility))
                    return utility

            # if it is possible to do in 2 roads
            elif self.would_give_us_longest(board, one_degree_roads):
                utility += longest_road_utility * (0.6666)
                if debug:
                    print("Road gives us access to a road that would give us longest road. Utility {}".format(
                        utility))

            # if it is possible to do in 3 roads
            elif self.would_give_us_longest(board, two_degree_roads):
                utility += longest_road_utility * (0.3333)
                if debug:
                    print(
                        "Road gives 3-degree access to longest road. Utility {}".format(utility))

        # settlement spots that we get access to with the given road
        one_degree_settlement_spots = self.get_potential_settlemnt_spots_with_roads(board, [
                                                                                    road])

        # should just be one. a road can only open up one new settlement spot at a time
        for settlement in one_degree_settlement_spots:
            utility += settlement_base_utility * \
                self.evaluateSettlement(board, settlement)
            if debug:
                print("Settlement Utility this road gives immediate access to: {}. Utility {}".format(
                    self.evaluateSettlement(board, settlement), utility))

        # exclude 1-degree spots
        two_degree_settlement_spots = self.get_potential_settlemnt_spots_with_roads(
            board, one_degree_roads)
        for settlement in one_degree_settlement_spots:
            if settlement in two_degree_settlement_spots:
                two_degree_settlement_spots.remove(settlement)

        if len(two_degree_settlement_spots) > 0:
            best_settlement = max(
                two_degree_settlement_spots, key=lambda settle: self.evaluateSettlement(board, settle))
            utility += (0.2) * settlement_base_utility * \
                self.evaluateSettlement(board, best_settlement)
            if debug:
                print("Settlement Utility this road gives 2-degree access to: {}. Utility {}".format(
                    self.evaluateSettlement(board, best_settlement), utility))

        # exclude 2-degree spots
        three_degree_settlement_spots = self.get_potential_settlemnt_spots_with_roads(
            board, two_degree_roads)

        for settlement in one_degree_settlement_spots + two_degree_settlement_spots:
            if settlement in three_degree_settlement_spots:
                three_degree_settlement_spots.remove(settlement)

        if len(three_degree_settlement_spots) > 0:
            best_settlement = max(three_degree_settlement_spots,
                                  key=lambda settle: self.evaluateSettlement(board, settle))
            utility += (0.1) * settlement_base_utility * \
                self.evaluateSettlement(board, best_settlement)
            if debug:
                print("Settlement Utility this road gives 3-degree access to: {}. Utility {}".format(
                    self.evaluateSettlement(board, best_settlement), utility))

        if self.would_increase_max_length(board, road):
            utility += increase_max_length_utility
            if debug:
                print("Road would increase max length. Utility {}".format(utility))
        if debug:
            print(one_degree_settlement_spots)
            print(two_degree_settlement_spots)
            print(three_degree_settlement_spots)
            print()

        return utility

    def get_potential_roads_with(self, board, roads):
        '''
        given a list of roads, return only the NEW roads that we would be able to place
        '''

        # double check that we are only using roads that we didnt already build
        new_roads = []
        for road in roads:
            if road not in self.buildGraph["ROADS"]:
                new_roads.append(road)

        # exclude any roads that we can already build
        exclude_list = list(board.get_potential_roads(self))

        # add the new roads to our build graph and boardgraph
        for road in new_roads:
            self.buildGraph["ROADS"].append(road)
            board.updateBoardGraph_road(road[0], road[1], self)

        new_potential_roads = list(board.get_potential_roads(self).keys())

        # remove the new roads from our build graph
        for road in new_roads:
            self.buildGraph["ROADS"].remove(road)
            board.remove_road_from_boardGraph(road[0], road[1])

        for road in exclude_list:
            if road in new_potential_roads:
                new_potential_roads.remove(road)

        return new_potential_roads

    def would_give_us_longest(self, board, roads):
        '''
        given a list of roads, return true if we would take longest road given the roads
        '''
        # if we can't take it, no roads would give us longest road
        if not self.can_take_longest_road():
            return False

        # double check that we are only using roads that we didnt already build
        new_roads = []
        for road in roads:
            if road not in self.buildGraph["ROADS"]:
                new_roads.append(road)

        # add the new roads to our build graph and boardgraph
        for road in new_roads:
            self.buildGraph["ROADS"].append(road)
            board.updateBoardGraph_road(road[0], road[1], self)

        max_length = self.get_road_length(board)

        could_take_longest = False
        # has to be at least 5
        if (max_length >= 5):
            could_take_longest = True
            for player in list(self.game.playerQueue.queue):
                # if another player has the same or longer length, we dont have longest
                if (player.maxRoadLength >= max_length and player != self):
                    could_take_longest = False

        # remove the new roads from our build graph
        for road in new_roads:
            self.buildGraph["ROADS"].remove(road)
            board.remove_road_from_boardGraph(road[0], road[1])

        return could_take_longest

    def would_increase_max_length(self, board, road):
        '''
        given a road, return true if it increases our max length
        '''
        # double check that the road hasn't already been build

        if road in self.buildGraph["ROADS"]:
            return False

        self.buildGraph["ROADS"].append(road)
        board.updateBoardGraph_road(road[0], road[1], self)

        max_length = self.get_road_length(board)

        self.buildGraph["ROADS"].remove(road)
        board.remove_road_from_boardGraph(road[0], road[1])

        return max_length > self.maxRoadLength

    def get_potential_settlemnt_spots_with_roads(self, board, roads):
        '''
        given a list of roads, return a list of settlement spots that we would be able to build at if the given roads were in our build graph

        DO NOT return settlements that are currently possible
        '''
        # double check that we are only using roads that we didnt already build
        new_roads = []
        for road in roads:
            if road not in self.buildGraph["ROADS"]:
                new_roads.append(road)

        # exclude any settlements we can already build
        exclude_list = list(board.get_potential_settlements(self).keys())

        # add the new roads to our build graph and boardgraph
        for road in new_roads:
            self.buildGraph["ROADS"].append(road)
            board.updateBoardGraph_road(road[0], road[1], self)

        new_settlements = list(board.get_potential_settlements(self).keys())

        # remove the new roads from our build graph and boardgraph
        for road in new_roads:
            self.buildGraph["ROADS"].remove(road)
            board.remove_road_from_boardGraph(road[0], road[1])

        for settlement in exclude_list:
            if settlement in new_settlements:
                new_settlements.remove(settlement)

        return new_settlements

    def place_best_settlement(self, board):
        possible_placements = board.get_potential_settlements(self)

        for settlement in possible_placements.keys():
            possible_placements[settlement] = self.evaluateSettlement(
                board, settlement)

        best_settlement = max(possible_placements, key=possible_placements.get)

        self.build_settlement(best_settlement, board)
        return

    def place_best_city(self, board):

        possible_placements = board.get_potential_cities(self)

        for city in possible_placements.keys():
            possible_placements[city] = self.evaluateSettlement(board, city)

        best_city = max(possible_placements, key=possible_placements.get)

        self.build_city(best_city, board)
        return

    def play_best_dev_card(self, board):
        # TODO
        # TODO
        # TODO
        # TODO
        # TODO
        # TODO
        # TODO
        # TODO

        # self.play_devCard(self.game)

        return

    def able_to_do(self, option):
        '''
        helper function given a key (string) determines whether we can immediately do said option
        with our current resources
        '''
        if option == "ROAD":
            return self.can_buy_road()
        elif option == "SETTLEMENT":
            return self.can_buy_settlement()
        elif option == "CITY":
            return self.can_buy_city()
        elif option == "BUY_DEV":
            return self.can_buy_dev_card()
        elif option == "PLAY_DEV":
            return self.can_play_dev_card()

    def able_to_trade_for(self, option):
        '''
        helper function given a key (string) determines whether we can trade with bank/ports to get desired item
        '''
        if option == "ROAD":
            return self.can_get_resources_through_trading({'ORE': 0, 'BRICK': 1,
                                                           'WHEAT': 0, 'WOOD': 1, 'SHEEP': 0})
        elif option == "SETTLEMENT":
            return self.can_get_resources_through_trading({'ORE': 0, 'BRICK': 1,
                                                           'WHEAT': 1, 'WOOD': 1, 'SHEEP': 1})
        elif option == "CITY":
            return self.can_get_resources_through_trading({'ORE': 3, 'BRICK': 0,
                                                           'WHEAT': 2, 'WOOD': 0, 'SHEEP': 0})
        elif option == "BUY_DEV":
            return self.can_get_resources_through_trading({'ORE': 1, 'BRICK': 0,
                                                           'WHEAT': 1, 'WOOD': 0, 'SHEEP': 1})
        elif option == "PLAY_DEV":
            return self.can_play_dev_card()

    def make_trades_for(self, option):
        '''
        helper function given a key (string) makes trades to get corresponding resources

        it assumes that it is possible!!!!!
        '''
        if option == "ROAD":
            return self.trade_for_resources({'ORE': 0, 'BRICK': 1,
                                             'WHEAT': 0, 'WOOD': 1, 'SHEEP': 0})
        elif option == "SETTLEMENT":
            return self.trade_for_resources({'ORE': 0, 'BRICK': 1,
                                             'WHEAT': 1, 'WOOD': 1, 'SHEEP': 1})
        elif option == "CITY":
            return self.trade_for_resources({'ORE': 3, 'BRICK': 0,
                                             'WHEAT': 2, 'WOOD': 0, 'SHEEP': 0})
        elif option == "BUY_DEV":
            return self.trade_for_resources({'ORE': 1, 'BRICK': 0,
                                             'WHEAT': 1, 'WOOD': 0, 'SHEEP': 1})
        elif option == "PLAY_DEV":
            # should not be reached
            return

    '''
    "desire"/utility functions. main goals for these is that they do the best thing when it is obvious. DONT BE STUPID!
    '''

    def get_road_desire(self, board):
        '''
        if we have no available SPOTS for roads, it is 0
        if we have no roads left (placed 15 aready) it is 0

        roads are desired if we dont have longest road and it would give us the win

        roads are desired if we have 0 possible settlement spots.

        roads are desired if we are tied for longest road

        for now, thats it
        '''
        utility = 0
        if (self.roadsLeft == 0) or len(board.get_potential_roads(self)) == 0:
            return utility

        # if it would give us the win
        if self.max_points - self.victoryPoints <= 2 and self.can_take_longest_road():
            # slightly below settlements and cities, because those are much easier to ensure the AI will win by
            # using. still greater than other optiosn that aren't game winning though,
            utility = 999
            return utility

        return max(self.evaluateRoad(board, road) for road in board.get_potential_roads(self))

        if self.maxRoadLength == max(player.maxRoadLength for player in list(self.game.playerQueue.queue)):
            utility += 12

        if len(board.get_potential_settlements(self)) == 0:
            utility += 12

        if self.maxRoadLength == max(player.maxRoadLength for player in list(self.game.playerQueue.queue)):
            utility += 12

        return utility

    def can_take_longest_road(self):
        '''
        if we have it we cant take it

        if anyone has a longer road than us, and it is longer by more roads than we can build, we can't take it

        otherwise if our current max length + number of roads we can build > current max length, we can

        IMPROVEMENT: currently it does not consider if it cant build the roads in a way that improves the road length, 
        only if it can build enough roads that would theoretically add to its max length
        '''

        # if we already have it we cant take it
        if self.longestRoadFlag:
            return False

        # cant take it if we cant buy enough roads to get to 5
        if self.maxRoadLength + self.number_of_roads_we_can_buy() < 5:
            return False

        current_longest_road_length = 0

        for player in list(self.game.playerQueue.queue):
            if player != self:
                current_longest_road_length = max(
                    current_longest_road_length, player.maxRoadLength)

        # if our current length + the amount of roads we can buy is more than the current longest road, then we can take it
        return current_longest_road_length < self.maxRoadLength + self.number_of_roads_we_can_buy()

    def number_of_roads_we_can_buy(self):

        return min(self.roadsLeft, int(min(self.resources["WOOD"], self.resources["BRICK"]) / 2))

    def get_settlement_desire(self, board):
        '''
        we dont care to settle if we have no spots or if we have no settlements left. (we do want to settle even if we dont have resources, though)

        a settlement is approximately as valuable as the production it provides. use evaluate function on settlements that we could possibly build

        we max out utility if we are 1 VP from winning
        '''
        # start with base utility because they give us VPs
        utility = 10

        if self.settlementsLeft == 0 or len(board.get_potential_settlements(self)) == 0:
            return 0

        # if it would give us the win
        if self.max_points - self.victoryPoints == 1:
            utility = 1000
            return utility

        utility += max(self.evaluateSettlement(board, settlement)
                       for settlement in board.get_potential_settlements(self))
        utility *= 10

        return utility

    def get_city_desire(self, board):
        '''
        a city is as useful as the production it provides. we can evaluate it as if it was another settlement in the same spot as an existing one

        we max out utility if we are 1 VP from winning
        '''
        utility = 0

        # if we have no cities left to use, or if we have no settlements on the board
        if self.citiesLeft == 0 or len(self.buildGraph["SETTLEMENTS"]) == 0:
            return utility

        # if it would give us the win
        if self.max_points - self.victoryPoints == 1:
            utility = 1000
            return utility

        utility += max(self.evaluateSettlement(board, settlement)
                       for settlement in board.get_potential_cities(self))
        utility *= 10
        return utility

    def get_buy_dev_desire(self, board):
        '''
        dev card should be somewhere in the middle. we kind of want to buy dev cards only if our production matches it well, 
        but we dont want to buy dev cards if it will ruin our other stuff
        '''
        # base medium utility
        utility = 20

        # for now thats all

        return utility

    def get_play_dev_desire(self, board):
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

        debug = False

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

    def trade_for_resources(self, desired_resources, just_one=False):
        '''
        desired resources is a dict from resource string to amount desired

        function uses 2:1 first, 3:1, then 4:1

        IMPROVEMENT: prioritize which item to trade differently
        '''

        debug = False

        theoretical_resources = copy.deepcopy(self.resources)

        # for each resource
        for resource in desired_resources.keys():
            theoretical_resources[resource] -= desired_resources[resource]

        # while we can't pay for the desired item
        while not all(theoretical_resources[resource] >= 0 for resource in theoretical_resources):
            if debug:
                print(theoretical_resources)

            has_traded = False

            # for all ports
            for port in self.portList:

                # if we have a 2:1 port
                if port[:3] == "2:1":
                    port_resource_type = port[4:]

                    # if we have 2 of the resource
                    if theoretical_resources[port_resource_type] >= 2:

                        # updated the theoretical resource count
                        theoretical_resources[port_resource_type] -= 2

                        for resource in theoretical_resources:
                            if theoretical_resources[resource] < 0:
                                theoretical_resources[resource] += 1

                                # actually make the trade with the bank
                                self.trade_with_bank(
                                    port_resource_type, resource)

                                # only do it once
                                has_traded = True
                                if just_one:
                                    return True
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

                            # make the trade for theoretical resources
                            theoretical_resources[trade_resource] -= 3

                            # add it to whatever we still need
                            for resource in theoretical_resources:
                                if theoretical_resources[resource] < 0:
                                    theoretical_resources[resource] += 1

                                    # actually make the trade with the bank
                                    self.trade_with_bank(
                                        trade_resource, resource)
                                    # only do it once
                                    has_traded = True

                                    if just_one:
                                        return True

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

                    # make the trade for theoretical resources
                    theoretical_resources[trade_resource] -= 4

                    # add it to whatever we still need
                    for resource in theoretical_resources:
                        if theoretical_resources[resource] < 0:
                            theoretical_resources[resource] += 1

                            # actually make the trade with the bank
                            self.trade_with_bank(trade_resource, resource)

                            # only do it once
                            has_traded = True
                            if just_one:
                                return True
                            break

                    # break to top of while loop if we did make a trade
                    break

            if has_traded:
                continue

            # if we ever go through the loop and don't make a trade, something may have gone wrong
            return False

        # should be fine if we reach here
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

                    opponent_adjacent_hexes = self.get_adjacent_hexes_for_player(board, player, exclude_selves=True)                    
                    opponent_adjacent_hexes.sort(reverse=True, key=lambda opp_hex: self.get_opponent_production_for_hex(board, opp_hex))

                    for opp_hex in opponent_adjacent_hexes and opp_hex in valid_robber_spots:
                        self.move_robber(opp_hex, board, player)
                        return

        # TODO: failsafe if somehow it all is not possible, just pick one that has most production next to someone with a card
        return

    def get_adjacent_hexes_for_player(self, board, player, exclude_selves=True):

        hexes = []
        for settlement in player.buildGraph["SETTLEMENTS"]:
            for adj_hex in board.boardGraph[settlement].adjacentHexList:
                if adj_hex not in hexes:
                    hexes.append(adj_hex)

        # if we want to exclude any tiles adjacent to us
        if exclude_selves:
            for settlement in self.buildGraph["SETTLEMENTS"]:
                for adj_hex in board.boardGraph[settlement].adjacentHexList:
                    if adj_hex in hexes:
                        hexes.remove(adj_hex)

        return hexes
    
    def get_opponent_production_for_hex(self, board, opp_hex):
        '''
        for a given hex, get its production points for each adjacent settlement/city and sum it

        do not include our pp for this
        '''
        output = 0

        base_prod_points = self.production_points_for_hex(board, opp_hex)

        # for each player
        for player in list(self.game.playerQueue.queue):
            
            # for each of their settlements
            for settlement in player.buildGraph["SETTLEMENTS"]:

                # if the hex is adjacent to t=it
                if opp_hex in board.boardGraph[settlement].adjacentHexList:

                    output += base_prod_points

                    # if it is a city, double it
                    if opp_hex in player.buildGraph["CITIES"]:
                        output += base_prod_points

        return output



    def play_knight(self, board):
        if self.devCardPlayedThisTurn:
            return

        print("{} is playing a KNIGHT...".format(self.name))

        self.place_robber(board)
        self.devCardPlayedThisTurn = True
        self.knightsPlayed += 1
        self.devCards["KNIGHT"] -= 1

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

    def discard_cards(self, board):
        '''
        Function for the AI to choose a set of cards to discard upon rolling a 7
        '''
        # get current goal, and discard whichever cards affect it least
        # out of remaining cards, discard in order of most to least

        goals = self.get_move_goals(board)
        goal = max(goals, key=goals.get)

        amount_to_discard = int(sum(self.resources.values()) / 2)

        if sum(self.resources.values()) > 7:
            print("\nPlayer {} has {} cards and needs to discard {} cards!".format(
                self.name, sum(self.resources.values()), amount_to_discard))
            print("{} discarding resources...".format(self.name))
            for i in range(amount_to_discard):
                self.discard_one_card_with_goal(goal)
        else:
            print("\nPlayer {} has {} cards and does not need to discard any cards!".format(
                self.name, sum(self.resources.values())))
            return

    def discard_one_card_with_goal(self, goal):
        # set preffered to resources that we would prefer to discard given a certain goal
        if goal == "ROAD":
            preferred = ["WHEAT", "ORE", "SHEEP"]
        elif goal == "SETTLEMENT":
            preferred = ["ORE"]
        elif goal == "CITY":
            preferred = ["WOOD", "BRICK", "SHEEP"]
        elif goal == "BUY_DEV":
            preferred = ["WOOD", "BRICK"]
        elif goal == "PLAY_DEV":
            preferred = ["WOOD", "BRICK", "SHEEP", "ORE", "WHEAT"]

        # sort them in descending order
        preferred.sort(
            reverse=True, key=lambda resource: self.resources[resource])

        for resource in preferred:
            # try to discard 1
            if self.resources[resource] > 0:
                print("{} discarding 1 {}".format(self.name, resource))
                self.resources[resource] -= 1

                # return if we do discard
                return

        # just try with all resources
        preferred = ["WOOD", "BRICK", "SHEEP", "ORE", "WHEAT"]
        # sort them in descending order
        preferred.sort(
            reverse=True, key=lambda resource: self.resources[resource])

        for resource in preferred:
            # try to discard 1
            if self.resources[resource] > 0:
                print("{} discarding 1 {}".format(self.name, resource))
                self.resources[resource] -= 1

                # return. this should always eventually return because we should never have called this with <7 cards
                return

    # Function to propose a trade -> give r1 and get r2
    # Propose a trade as a dictionary with {r1:amt_1, r2: amt_2} specifying the trade
    # def propose_trade_with_players(self):

    # Function to accept/reject trade - return True if accept
    # def accept_trade(self, r1_dict, r2_dict):
