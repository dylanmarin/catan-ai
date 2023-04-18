# Settlers of Catan
# Dylan AI class implementation

from board import *
from player import *
import numpy as np
import copy
import time

# Class definition for an AI player


class dylanAIPlayer(player):

    # DYLAN: Added params to give initial preference to different resources/ port/resource_diversity
    def updateAI(self, game, ore=4, brick=4, wheat=4, wood=4, sheep=4, port_desire=0.85, resource_diversity_desire=0.6):
        self.isAI = True

        # Initialize resources with just correct number needed for set up (2 settlements and 2 road)
        # Dictionary that keeps track of resource amounts
        self.resources = {'ORE': 0, 'BRICK': 4,
                          'WHEAT': 2, 'WOOD': 4, 'SHEEP': 2}

        # DYLAN: Moved their diceRoll_expectation dict into a class var. This is equivalent to production points conversion
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


        '''
        static dicts of costs for each item
        '''
        self.road_cost = {'ORE': 0, 'BRICK': 1,
                          'WHEAT': 0, 'WOOD': 1, 'SHEEP': 0}
        self.city_cost = {'ORE': 3, 'BRICK': 0,
                          'WHEAT': 2, 'WOOD': 0, 'SHEEP': 0}
        self.settlement_cost = {'ORE': 0, 'BRICK': 1,
                                'WHEAT': 1, 'WOOD': 1, 'SHEEP': 1}
        self.buy_dev_cost = {'ORE': 1, 'BRICK': 0,
                             'WHEAT': 1, 'WOOD': 0, 'SHEEP': 1}

        self.option_to_resources_required_dict = \
            {"BUY_DEV": self.buy_dev_cost,
             "SETTLEMENT": self.settlement_cost,
             "CITY": self.city_cost,
             "ROAD": self.road_cost}

        self.game = game

        print("Added new AI Player: ", self.name)


    # Function to build an initial settlement 
    def initial_setup(self, board):

        # get the best setup settlement placement according to our settlement evaluation
        best_placement = self.get_best_setup_settlement(board)

        self.build_settlement(best_placement, board)


        # use our place_best_road function with setup flag=True so that it only looks at setup roads
        self.place_best_road(board, setup=True)

    def get_best_setup_settlement(self, board, exclude=[]):
        ''' 
        given all possible setup settlements on the board, just take the max according to our evaluate settlement function
        '''
        possible_placements = {}
        for placement in board.get_setup_settlements(self).keys():
            # if we want to exclude it, dont add it
            if placement not in exclude:
                possible_placements[placement] = 0

        for p in possible_placements.keys():
            possible_placements[p] = self.evaluate_settlement(board, p)

        # get the placement with the max value
        return max(possible_placements, key=possible_placements.get)

    def evaluate_settlement(self, board, settlement_location):
        '''
        multiply production by desire for that production

        add rating of ports usable by this our current settlements in addition to this
        hypothetical settlement to the rating

        use self.resource_diversity_desire to scale our desire for resource diversity

        add resource synergy to the eval
        '''
        debug = False

        total_rating = 0

        # Evaluate based on production points of surrounding hexes

        # for each resource type
        for resourceType in self.resourcePreferences.keys():
            # add the production points of that resource for this settlement to the rating

            production_points = self.get_production_points_for_settlement(
                board, resourceType, settlement_location)

            total_rating += production_points * \
                self.resourcePreferences[resourceType]

            # if this settlement produces resourceType
            if production_points > 0:
                # then we add a diversity score multiplied by how much we care about resource diversity
                total_rating += self.resource_diversity_desire * \
                    self.get_diversity_of_settlement(board, settlement_location)


        port = board.boardGraph[settlement_location].port
        # if there is a port
        if port:
            # multiply the addition by self.port_desire
            total_rating += self.port_desire * \
                self.evaluate_port(board, port, settlement_location)

        # add resource synergy
        total_rating += self.resource_synergy_in_setup(
            board, settlement_location)

        if debug:
            print("Rating of settlement: {}".format(total_rating))

        return total_rating

    def evaluate_port(self, board, port, hypothetical_settlement):
        '''
        evaluate a given port on a board for this player

        with the hypothetical settlement option, if given it evaluates the port as 
        if the settlement exists in our setup already
        '''
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
                self.get_our_production_points(
                    board, port_resource_type, hypothetical_settlement)
        else:
            # if it is 3:1 add scaled down value proportional to total production points for all resources
            for resource_type in self.resources.keys():
                total_value += 0.33 * \
                    self.get_our_production_points(
                        board, resource_type, hypothetical_settlement)

        if debug:
            print("Eval for {} is {}".format(port, str(total_value)))

        return total_value

    def get_our_production_points(self, board, resource, hypothetical_settlement):
        '''
        Returns our production points for a given resource. If hypothetical settlement is included,
        add the amount that it provides.

        Production points is the number of ways to roll the number assigned to a hex. It is stored 
        statically in self.diceRoll_expectation
        '''

        total_prod = 0

        # for each settlement
        for settlement in self.buildGraph["SETTLEMENTS"]:
            total_prod += self.get_production_points_for_settlement(
                board, resource, settlement)

        if hypothetical_settlement:
            total_prod += self.get_production_points_for_settlement(
                board, resource, hypothetical_settlement)

        return total_prod

    def get_production_points_for_settlement(self, board, resource, settlement):
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

    def get_diversity_of_settlement(self, board, settlement_location):
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
            max_prod_for_type[resource_type] = self.get_our_production_points(
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
            settlement_production_points[resource] = self.get_production_points_for_settlement(
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

        # TODO: was unable to finish the overall setup synergy

        if had_more_time:
            our_production_points = {}

            for resource in self.resourcePreferences:
                our_production_points[resource] = self.get_our_production_points(
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

    def move(self, board):
        print("{}'s TURN...".format(self.name))
        '''
        Note: read the project report for a more legible and less technical explanation of this code.

        Options:
        -road
        -settlement
        -city
        -buy a dev card

        also:
        play a dev card
        propose a trade
            - to players
            - with port or bank

        flow:

        resources blocked OR it will give us largest army OR put us ahead in a current tie of knights:
            play knight

        roll

        discard cards if necessary
        move robber if blocked

        check which options are possible:
            road
            settlement
            city
            buy_dev

        get utility for all options:
            this utility is the desire function for each option
                settlement and city can both use settlement evaluate
                road utility probs has something to do with settlements it opens up
                buying dev card "utility" probably wins out when our production aligns with dev cards, and when we cant do other options

        for each possible option, in order of their utility/desire:
            if we can do it, do it

            if we can't, see if we can make trades with the bank that help us
                if we can do trade in order to do it, trade and try to do our option again

            if we can't and there are no trades, see if we have a dev card that helps us
                if we do, play it and try to do our option again

            if we can't do it, and we have no useful dev card:
                offer a trade to other players. 

            if at any point we did something (changed the state)
                check all of our options again
            if we try for all of our options and cant do anything,
                finish our turn
        '''
        debug = False
        # we may have already played a knight before rolling
        # may have rolled a 7 and moved the robber AND discarded cards

        # (takes into account if we have already played a knight)
        if self.should_play_knight_after_rolling(board):
            # NOTE: does not take into account whether waiting to play another dev card is better
            self.play_knight(board)

        # able to do something basically represents whether we were able to do anything. 
        # as long as we were able to do something, evaluate our options again
        able_to_do_something = True
        while able_to_do_something:
            # assume we wont be able to do anything
            able_to_do_something = False

            # we havent yet made a successful trade
            made_successful_trade = False

            # get our goals (and their desires)
            move_goals = self.get_move_goals(board)

            # get just the option string
            options = list(move_goals.keys())
            # sort them based on desire
            options.sort(
                reverse=True, key=lambda goal: move_goals[goal])

            # in order of desire
            for option in options:
                # if the desire/utility is 0, skip this option
                if move_goals[option] == 0:
                    continue

                if debug:
                    print("{} desire: {}".format(option, move_goals[option]))

                # if we can do our option
                if self.able_to_do(option, board):
                    if debug:
                        print("Able to: {}".format(option))

                    # do it
                    self.make_move(board, option)

                    # anytime we do an option, we do it and go back to top of loop
                    able_to_do_something = True
                    break

                elif self.able_to_trade_for(option):
                    # if we can trade for our option
                    if debug:
                        print("Able to: {}".format(option))

                    # make the trades
                    self.make_trades_for(option)

                    # do it
                    self.make_move(board, option)

                    # anytime we do an option, we do it and go back to top of loop
                    able_to_do_something = True
                    break
                else:
                    # if we couldnt trade for it see if we can play a dev card for it

                    # if we want to build a road and it is our first choice option
                    if max(move_goals, key=move_goals.get) == "ROAD" and option == "ROAD":
                        # if we have roadbuilding
                        if self.can_play_roadbuilder():
                            # play it
                            self.play_roadbuilder(board)
                            able_to_do_something = True
                            break
                        if debug:
                            print(
                                "Can't play roadbuilding for {}".format(option))

                    # if our current option is our first choice
                    if max(move_goals, key=move_goals.get) == option:
                        # if we can play a year of plenty
                        if self.can_play_year_of_plenty():
                            # if we can build it by playing YoP  (we need exactly 2 cards)
                            if self.can_build_with_year_of_plenty(option):
                                # play the yop
                                self.play_year_of_plenty_for(option)
                                able_to_do_something = True
                                break
                            if debug:
                                print(
                                    "Can't use year of plenty for {}".format(option))

                        # if we can play a monopoly
                        if self.can_play_monopoly():
                            # if we can build by monopolying
                            if len(self.can_build_with_monopoly(option, board)) > 0:
                                self.play_monopoly(option, board)
                                able_to_do_something = True
                                break
                            if debug:
                                print(
                                    "Can't use monopoly for {}".format(option))

                    # if we have < 7 cards and couldnt play a dev card,
                    # discard lower rated options that will hinder our current goal
                    # ie discard road if our current option is settlement
                    if sum(self.resources.values()) <= 7:
                        goals_to_remove = self.get_conflicting_goals(
                            option, options)
                        for goal_to_remove in goals_to_remove:
                            if goal_to_remove in options:
                                options.remove(goal_to_remove)

                    # while we have more than 7 cards, trade towards our highest rated option
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

                            # NOTE: IMPROVEMENT: it's been a while since i looked at this and dont want to mess anything up last minute, 
                            # but this could probably be removed if I just put the if <= 7 cards check below the loop
                            goals_to_remove = self.get_conflicting_goals(
                                option, options)
                            for goal_to_remove in goals_to_remove:
                                if goal_to_remove in options:
                                    options.remove(goal_to_remove)
                        else:
                            if debug:
                                print("{} was unable to trade for {} and still has {} cards".format(
                                    self.name, option, sum(self.resources.values())))
                            # if we couldn't trade for something, then we can keep lower rated options in the queue
                            # cant trade or play any devs. just break
                            break

                    # we have gone through all options
                    # cant build it
                    # cant roadbuilder, year of plenty, or monopoly for it
                    # cant port for it

                    # then:
                    # try trading with other players for a resource we want

                    # if this option is our first choice
                    if max(move_goals, key=move_goals.get) == option:
                        # if we haven't already made a trade this turn
                        if not made_successful_trade:
                            # if we successfully made a trade
                            if self.propose_trade(board, option):
                                # try again since we got something we wanted
                                able_to_do_something = True
                                made_successful_trade = True
                                break
                            else:
                                if debug:
                                    print("Tried to make a trade but was unable to")

                    # if we couldnt trade for it continue to next option
                    continue

        # after we've tried all options pass our turn
        return

    def can_play_monopoly(self):
        # can play amonopoly if we have the card and haven't played a dev card yet
        return self.devCards["MONOPOLY"] > 0 and not self.devCardPlayedThisTurn

    def can_build_with_monopoly(self, option, board):
        '''
        function to check that if we can build a given option with a monopoly on one of the resources
        '''
        valid_resource_options = []

        # for each resource option
        for resource in self.resources.keys():
            hypothetical_additional_resources = {
                'ORE': 0, 'BRICK': 0, 'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}
            
            # add to the hypothetical resources the amount that we would get for monopolying
            hypothetical_additional_resources[resource] = self.get_opponent_count(
                resource)

            # if we are able to do a given option with the extra resources OR if we can trade for an option with those extra resources
            if self.able_to_do(option, board, hypothetical_additional_resources) or self.able_to_trade_for(option, hypothetical_additional_resources):
                # add the resource as a valid option
                valid_resource_options.append(resource)

        return valid_resource_options

    def get_opponent_count(self, resource):
        '''
        assumes the ai player has perfect knowledge of opponent card count. 

        technically possible for humans who track what numbers have been rolled, so only slightly cheating

        returns int amount of resource that all other players have
        '''
        count = 0
        for player in list(self.game.playerQueue.queue):
            if player != self:
                count += player.resources[resource]
        return count

    def play_monopoly(self, option, board):
        '''
        assuming that we CAN build an option with a monopoly played,
        we pick from the valid resources for the given option whichever resource 
        would result in the most resources acquired

        TODO: incorporate the idea that fewer cards may be better because of different port access
        '''

        # get valid options. assume one exists
        resource_options = self.can_build_with_monopoly(option, board)

        # backup incase there is no valid option
        if len(resource_options) == 0:
            return

        # get the resource that has the most cards
        best_resource = max(
            resource_options, key=lambda resource: self.get_opponent_count(resource))
        
    
        resources_taken = 0

        # for each player
        for player in list(self.game.playerQueue.queue):
            if (player != self):
                # take those cards
                self.resources[best_resource] += player.resources[best_resource]
                resources_taken += player.resources[best_resource]
                player.resources[best_resource] = 0

        print("Playing MONOPOLY. Stole {} {}".format(
            resources_taken, best_resource))
        self.devCardPlayedThisTurn = True
        self.devCards["MONOPOLY"] -= 1
        return

    def can_play_year_of_plenty(self):
        # check if we haven't played a dev card and we have a year of plenty
        return self.devCards["YEAROFPLENTY"] > 0 and not self.devCardPlayedThisTurn

    def can_build_with_year_of_plenty(self, option):
        '''
        check if we need exactly two resources for the option that we want to build

        ensures we dont waste a year of plenty
        '''
        resources_needed = self.get_resources_needed_for(option)

        return sum(resources_needed.values()) == 2

    def get_resources_needed_for(self, option):
        '''
        returns a dict of resources with the amount we need to build the given option
        '''
        option_cost = self.option_to_resources_required_dict[option]

        resource_need_dict = {}

        for resource, cost in option_cost.items():
            # the amount we have
            current = self.resources[resource]

            # the cost minus what we have, bounded to 0
            need = max(cost - current, 0)

            resource_need_dict[resource] = need

        return resource_need_dict

    def play_year_of_plenty_for(self, option):
        '''
        assumes we need exactly 2 resources, since that is the only time its called
        '''

        print("{} playing YEAROFPLENTY...".format(self.name))
        resources_needed = self.get_resources_needed_for(option)
        resources_bought = 0

        for resource, cost in resources_needed.items():
            if resources_bought == 2:
                break
            
            if cost == 2:
                self.resources[resource] += 2
                print("Using YEAROFPLENTY for 2 {}".format(resource))
                resources_bought += 2
            elif cost == 1:
                self.resources[resource] += 1
                print("Using YEAROFPLENTY for 1 {}".format(resource))
                resources_bought += 1

        # NOTE: Code was changed so that YOP is only played when we need exactly 2 cards, so this shouldn't be reached OR needed anymore
        while resources_bought < 2:
            # TODO: DONT randomly pick a resource
            random_resource = list(self.resources.keys())[
                np.random.randint(0, 5)]
            self.resources[random_resource] += 1
            print("Using YEAROFPLENTY for 1 {}".format(random_resource))
            resources_bought += 1

        self.devCardPlayedThisTurn = True
        self.devCards["YEAROFPLENTY"] -= 1
        return

    def can_play_roadbuilder(self):
        # if we have the card and havent played a dev yet
        return self.devCards["ROADBUILDER"] > 0 and not self.devCardPlayedThisTurn

    def play_roadbuilder(self, board):
        ''' 
        if we can play the road builder

        place the next best 2 roads

        road_builder = True flag makes sure that it places the roads for free
        '''
        if self.can_play_roadbuilder():
            print("Playing ROADBUILDER")
            # place 2 free roads
            self.place_best_road(board, road_builder=True)
            self.place_best_road(board, road_builder=True)

            # subtract the card
            self.devCards["ROADBUILDER"] -= 1

            #
            self.devCardPlayedThisTurn = True

        return

    def get_conflicting_goals(self, current_goal, all_options):
        '''
        given the current goal, return any option that would disallow us to build the current goal

        takes into account if we have an excess of a specific resource OR if we don't have any of a specific resource

        ie. our top goal is settlement. we have 2 bricks 2 wood, 1 wheat and 0 sheep.
        we cant build a settlement but we dont need to remove the option to build a road, since it wouldnt affect our
        ability to build 1 settlement in the future
        '''
        debug = False
        goals_to_remove = []

        # for each option
        for option in all_options:
            # if its not our current goal or PLAY_DEV
            if option != current_goal or option == "PLAY_DEV":
                if debug:
                    print("Checking if {} conflicts with {}".format(
                        option, current_goal))
                    
                # if we cant build it without breaking it
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

        ie. our current goal is settlement and our breaking option is road. we have 2 bricks 2 wood, 1 wheat and 0 sheep.
        building a road would not break our settlement, since it wouldnt affect our
        ability to build 1 settlement in the future
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
                print(" If we built {}, we'd have {} remaining for {}".format(
                    breaking_option, current_amount-possible_breaking_amount, build_option))

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
                 "CITY": 0, "BUY_DEV": 0}

        goals["ROAD"] = self.get_road_desire(board)
        goals["SETTLEMENT"] = self.get_settlement_desire(board)
        goals["CITY"] = self.get_city_desire(board)
        goals["BUY_DEV"] = self.get_buy_dev_desire(board)

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
        return

    def place_best_road(self, board, setup=False, road_builder=False):
        '''
        two main ways to place road:
            use our evaluate_road function and place the road with the highest value
        '''

        possible_roads = board.get_potential_roads(self)

        if setup:
            possible_roads = board.get_setup_roads(self)

        best_road = max(possible_roads, key=lambda road: self.evaluate_road(
            board, road, setup=setup))

        self.build_road(best_road[0], best_road[1],
                        board, road_builder=road_builder)
        return

    def evaluate_road(self, board, road, debug=False, setup=False):
        '''
        function to evaluate roads


        if it gives us longest road, apply some utility
            if it would give us longest road for the win, apply MAX utility

        if it is within 2 roads of giving us largest road, apply 2/3 the amount

        if it is within 3 roads of giving us largest road, apply 1/3 the amount

        if it allows us to settle at a spot, add settlement_base_utility times the evaluation for that settlement

        if it allows us to build another road that will allow us to settle, do small constant times the base_utility times max value of the settlement

        if it is the first of 3 roads towards a settlement, do the above but with smaller constant

        if it increases max road length, apply medium amount of utility

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

        # new roads that we can build given the one_degree roads
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

        # if we can build more settlements, potential settlement spots should be taken into account
        if self.settlementsLeft >= 1:

            # settlement spots that we get access to with the given road
            one_degree_settlement_spots = self.get_potential_settlemnt_spots_with_roads(board, [
                                                                                        road])

            # should just be one. a road can only open up one new settlement spot at a time
            for settlement in one_degree_settlement_spots:
                utility += settlement_base_utility * \
                    self.evaluate_settlement(board, settlement)
                if debug:
                    print("Settlement Utility this road gives immediate access to: {}. Utility {}".format(
                        self.evaluate_settlement(board, settlement), utility))

            # exclude 1-degree spots
            two_degree_settlement_spots = self.get_potential_settlemnt_spots_with_roads(
                board, one_degree_roads)
            for settlement in one_degree_settlement_spots:
                if settlement in two_degree_settlement_spots:
                    two_degree_settlement_spots.remove(settlement)

            # if there are any 2 degree spots
            if len(two_degree_settlement_spots) > 0:

                # take the best one
                best_settlement = max(
                    two_degree_settlement_spots, key=lambda settle: self.evaluate_settlement(board, settle))
                
                # add some small amount times the utility
                utility += (0.2) * settlement_base_utility * \
                    self.evaluate_settlement(board, best_settlement)
                
                if debug:
                    print("Settlement Utility this road gives 2-degree access to: {}. Utility {}".format(
                        self.evaluate_settlement(board, best_settlement), utility))

            # exclude 1-degree and 2-degree spots
            three_degree_settlement_spots = self.get_potential_settlemnt_spots_with_roads(
                board, two_degree_roads)

            for settlement in one_degree_settlement_spots + two_degree_settlement_spots:
                if settlement in three_degree_settlement_spots:
                    three_degree_settlement_spots.remove(settlement)

            # if there are 3-degree spots
            if len(three_degree_settlement_spots) > 0:

                # take the best settlement
                best_settlement = max(three_degree_settlement_spots,
                                      key=lambda settle: self.evaluate_settlement(board, settle))
                
                # multiply times some smaller utility
                utility += (0.1) * settlement_base_utility * \
                    self.evaluate_settlement(board, best_settlement)
                
                if debug:
                    print("Settlement Utility this road gives 3-degree access to: {}. Utility {}".format(
                        self.evaluate_settlement(board, best_settlement), utility))

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
        given a list of roads, return only the NEW roads that we would be able to place if the given roads were built
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

        # use built in function to get road length now
        max_length = self.get_road_length(board)

        could_take_longest = False
        # has to be at least 5
        if (max_length >= 5):

            # if we have at least 5 roads
            could_take_longest = True

            # check that no player has a longer or equal length road already 
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
        given a single road, return true if it increases our max length
        '''
        # double check that the road hasn't already been build

        if road in self.buildGraph["ROADS"]:
            return False

        # add the road to our build and board graph
        self.buildGraph["ROADS"].append(road)
        board.updateBoardGraph_road(road[0], road[1], self)

        # use builnt in function to get road length
        max_length = self.get_road_length(board)

        # remove hypothetical road
        self.buildGraph["ROADS"].remove(road)
        board.remove_road_from_boardGraph(road[0], road[1])

        # check if our length has increased
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

        # use built in function to get potential settlements
        new_settlements = list(board.get_potential_settlements(self).keys())

        # remove the new roads from our build graph and boardgraph
        for road in new_roads:
            self.buildGraph["ROADS"].remove(road)
            board.remove_road_from_boardGraph(road[0], road[1])

        # remove settlements we already had
        for settlement in exclude_list:
            if settlement in new_settlements:
                new_settlements.remove(settlement)

        return new_settlements

    def place_best_settlement(self, board):
        '''
        get all possible settlement spots, and using our evaluation function, build the best one
        '''
        possible_placements = board.get_potential_settlements(self)

        for settlement in possible_placements.keys():
            possible_placements[settlement] = self.evaluate_settlement(
                board, settlement)

        best_settlement = max(possible_placements, key=possible_placements.get)

        self.build_settlement(best_settlement, board)
        return

    def place_best_city(self, board):
        '''
        get all possible city spots, and using our **settlement** evaluation function, build the best one
        '''
        possible_placements = board.get_potential_cities(self)

        for city in possible_placements.keys():
            possible_placements[city] = self.evaluate_settlement(board, city)

        best_city = max(possible_placements, key=possible_placements.get)

        self.build_city(best_city, board)
        return

    '''
    UNUSED 
    def play_best_dev_card(self, board):
        return
    '''

    def able_to_do(self, option, board, hypothetical_extra_resources={'ORE': 0, 'BRICK': 0,
                                                                      'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}):
        '''
        helper function given a key (string) determines whether we can immediately do said option
        with our current resources
        '''
        if option == "ROAD":
            return self.can_buy_road(hypothetical_extra_resources)
        elif option == "SETTLEMENT":
            return self.can_buy_settlement(hypothetical_extra_resources)
        elif option == "CITY":
            return self.can_buy_city(hypothetical_extra_resources)
        elif option == "BUY_DEV":
            return self.can_buy_dev_card(board, hypothetical_extra_resources)
        return False

    def able_to_trade_for(self, option, hypothetical_extra_resources={'ORE': 0, 'BRICK': 0,
                                                                      'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}):
        '''
        helper function given a key (string) determines whether we can trade with bank/ports to get desired item

        assumes we have these hypothetical extra resources as well
        '''
        if option == "ROAD":
            return self.can_get_resources_through_trading({'ORE': 0, 'BRICK': 1,
                                                           'WHEAT': 0, 'WOOD': 1, 'SHEEP': 0}, hypothetical_extra_resources)
        elif option == "SETTLEMENT":
            return self.can_get_resources_through_trading({'ORE': 0, 'BRICK': 1,
                                                           'WHEAT': 1, 'WOOD': 1, 'SHEEP': 1}, hypothetical_extra_resources)
        elif option == "CITY":
            return self.can_get_resources_through_trading({'ORE': 3, 'BRICK': 0,
                                                           'WHEAT': 2, 'WOOD': 0, 'SHEEP': 0}, hypothetical_extra_resources)
        elif option == "BUY_DEV":
            return self.can_get_resources_through_trading({'ORE': 1, 'BRICK': 0,
                                                           'WHEAT': 1, 'WOOD': 0, 'SHEEP': 1}, hypothetical_extra_resources)

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
        return

    '''
    "desire"/utility functions. main goals for these is that they do the best thing when it is obvious. DONT BE STUPID!
    '''
    def get_road_desire(self, board):
        '''
        if we have no available SPOTS for roads, it is 0
        if we have no roads left (placed 15 aready) it is 0

        roads are desired if we dont have longest road and we can take longest road for the win

        otherwise just use the max utility of all road options
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

        return max(self.evaluate_road(board, road) for road in board.get_potential_roads(self))

    def can_take_longest_road(self):
        '''
        if we have it we cant take it

        if anyone has a longer road than us, and it is longer by more roads than we can build, we can't take it

        otherwise if our current max length + number of roads we can afford currently > current max length, we can

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
        # whichever is smaller between the roads we can afford and the number of roads we have left to build
        return min(self.roadsLeft, int(min(self.resources["WOOD"], self.resources["BRICK"]) / 2))

    def get_settlement_desire(self, board):
        '''
        we dont care to settle if we have no spots or if we have no settlements left. (we do want to settle even if we dont have resources, though)

        we want to build a settlement propotionately as much as the utility of the best rated settlement option 
        we multiply the utility by 10 to get it on a similar scale to roads and other options

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

        utility += max(self.evaluate_settlement(board, settlement)
                       for settlement in board.get_potential_settlements(self))
        utility *= 10

        return utility

    def get_city_desire(self, board):
        '''
        zero out utility if we have none left or have no settlements to upgrade

        we max out utility if we are 1 VP from winning

        otherwise a city is desired propotionately as much as the utility of our best rated city option
        we multiply the utility by 10 to get it on a similar scale to roads and other options

        if we have no settlements left to build, we want to increase the city desire, since it will allow us to build more settlements.
        helps prioritize against roads when we have no more settlements elft
        '''
        utility = 0

        # if we have no cities left to use, or if we have no settlements on the board
        if self.citiesLeft == 0 or len(self.buildGraph["SETTLEMENTS"]) == 0:
            return utility

        # if it would give us the win
        if self.max_points - self.victoryPoints == 1:
            utility = 1000
            return utility

        utility += max(self.evaluate_settlement(board, settlement)
                       for settlement in board.get_potential_cities(self))
        utility *= 10

        # increase utility if we already have 5 settlements
        if self.settlementsLeft == 0:
            utility *= 2.5

        return utility

    def get_buy_dev_desire(self, board):
        '''
        dev card should be somewhere in the middle. we kind of want to buy dev cards only if our production matches it well,
        but we dont want to buy dev cards if it will ruin our other stuff
        '''
        # base medium utility
        utility = 20

        if sum(board.devCardStack.values()) == 0:
            return 0

        # if we have no dev cards outside of vps, we want at least 1
        if sum(self.devCards.values()) + len(self.newDevCards) <= self.devCards["VP"]:
            utility += 5

        # if we specifically have no knights as well add some value
        if self.devCards["KNIGHT"] == 0 and "KNIGHT" not in self.newDevCards:
            utility += 5

        return utility

    '''
    helper functions to tell us if we can AFFORD to do something. does not check if we have enough of that item left. 
    
    they each take in some hypothetical resources that are used in considering which dev cards to play
    '''

    def can_buy_road(self, hypothetical_extra_resources={'ORE': 0, 'BRICK': 0,
                                                         'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}):
        return self.resources["BRICK"] + hypothetical_extra_resources["BRICK"] > 0 \
            and self.resources["WOOD"] + hypothetical_extra_resources["WOOD"] > 0

    def can_buy_settlement(self, hypothetical_extra_resources={'ORE': 0, 'BRICK': 0,
                                                               'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}):
        return self.resources["BRICK"] + hypothetical_extra_resources["BRICK"] > 0 \
            and self.resources["WOOD"] + hypothetical_extra_resources["WOOD"] > 0 \
            and self.resources["SHEEP"] + hypothetical_extra_resources["SHEEP"] > 0 \
            and self.resources["WHEAT"] + hypothetical_extra_resources["WHEAT"] > 0

    def can_buy_city(self, hypothetical_extra_resources={'ORE': 0, 'BRICK': 0,
                                                         'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}):
        return self.resources["WHEAT"] + hypothetical_extra_resources["WHEAT"] >= 2 \
            and self.resources["ORE"] + hypothetical_extra_resources["ORE"] >= 3

    def can_buy_dev_card(self, board, hypothetical_extra_resources={'ORE': 0, 'BRICK': 0,
                                                                    'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}):

        if sum(board.devCardStack.values()) > 0:
            return self.resources["ORE"] + hypothetical_extra_resources["ORE"] > 0 \
                and self.resources["SHEEP"] + hypothetical_extra_resources["SHEEP"] > 0 and \
                self.resources["WHEAT"] + \
                hypothetical_extra_resources["WHEAT"] > 0
        else:
            return False

    def can_get_resources_through_trading(self, desired_resources, hypothetical_extra_resources):
        '''
        desired resources is a dict from resource string to amount desired

        hypothetical resources is a dict of resource string to the amount we want to imagine having in this calculation

        function checks if through 4:1, 3:1, 2:1 trading it can reach the desired resources

        returns true if it is possible
        '''

        debug = False

        # make a copy of our current resources that will be used to calculate if we can trade for it
        theoretical_resources = copy.deepcopy(self.resources)

        # for each resource
        for resource in desired_resources.keys():
            # add the hypothetical extra resources
            theoretical_resources[resource] += hypothetical_extra_resources[resource]

            # subtract the amount we want
            theoretical_resources[resource] -= desired_resources[resource]

        # while any theoretical resource is negative
        while not all(theoretical_resources[resource] >= 0 for resource in theoretical_resources):
            if debug:
                print(theoretical_resources)

            has_traded = False

            # try each port
            for port in self.portList:

                # if we have a 2:1 port
                if port[:3] == "2:1":
                    port_resource_type = port[4:]
                    if debug:
                        print("Checking 2:1 {} options...".format(
                            port_resource_type))

                    # if we have 2 of the item remaining
                    if theoretical_resources[port_resource_type] >= 2:

                        # hypothetically make the trade
                        theoretical_resources[port_resource_type] -= 2

                        # add 1 resource to whichever resource needs it
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

            # no port trade, so try 4:1

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

        if just_one is true, just make the first trade we calculate

        returns True if trades are made successfully

        ASSUMES at least one trade is possible

        IMPROVEMENT: prioritize which item to trade differently
        '''

        debug = False

        # copy our resources to aid in calculation
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

                                # finish if we made a trade
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

                                    # finish if we made a trade
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

                            # finish if we made a trade
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
        '''
        if we are blocked, and we have fewer than or more than 7 cards, we should play the knight (if we have one)

        if we are blocked and half exactly 7 cards, play the knight 5/6 times.

        NOTE: Doesn't take into account value of staying blocked but playing a different dev card later in the turn
        '''

        # if we dont have a knight or already played one
        if self.devCards["KNIGHT"] == 0 or self.devCardPlayedThisTurn:
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
            if they don't have dev cards, we can wait since they cant overtake us
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
        '''
        sort opponent players by VPs (ai is given perfect knowledge)

        for each opponent, while we havent placed the robber, get all adjacent hexes to their settlements

        if the hex isnt adjacent to us, and didnt have the robber on it before, place it on whichever hex has the most production output
        its own production points times the number of settlements adjacent to it. (+1 for cities)
        
        '''
        print("{} is moving the robber...".format(self.name))

        debug = True

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

        # check if all opponents have the same amount of vp
        if self.all_opponents_tied_for_vps():

            # place on hex that is not adjacent to us with most production
            all_valid_hexes = []

            for player in all_players:
                # skip ourselves
                if player != self:
                    opponent_adjacent_hexes = self.get_adjacent_hexes_for_player(
                        board, player, exclude_selves=True)
                    for adj_hex in opponent_adjacent_hexes:
                        if adj_hex not in all_valid_hexes:
                            all_valid_hexes.append(adj_hex)

            # sort them from most opponent production to least
            all_valid_hexes.sort(
                reverse=True, key=lambda opp_hex: self.get_opponent_production_for_hex(board, opp_hex))

            for opp_hex in all_valid_hexes:
                if opp_hex in valid_robber_spots:

                    if debug:
                        print("Moving to hex {}. Production blocked: {}".format(
                            opp_hex, self.get_opponent_production_for_hex(board, opp_hex)))

                    self.move_robber(opp_hex, board, player)
                    return

        else:
            # for each opponents with at least one card (or if all opponents have 0 cards then all of them)
            for player in all_players:
                # skip ourselves
                if player != self:

                    # if this player has cards, or if everyone has zero cards
                    if sum(player.resources.values()) > 0 or all_have_zero:

                        if debug:
                            print("Attempting to rob from {}".format(player.name))

                        opponent_adjacent_hexes = self.get_adjacent_hexes_for_player(
                            board, player, exclude_selves=True)
                        opponent_adjacent_hexes.sort(
                            reverse=True, key=lambda opp_hex: self.get_opponent_production_for_hex(board, opp_hex))

                        for opp_hex in opponent_adjacent_hexes:
                            if opp_hex in valid_robber_spots:

                                if debug:
                                    print("Moving to hex {}. Production blocked: {}".format(
                                        opp_hex, self.get_opponent_production_for_hex(board, opp_hex)))

                                self.move_robber(opp_hex, board, player)
                                return

        # TODO: failsafe if somehow it all is not possible, just pick one that has most production next to someone with a card
        # right now it just moves it to the last hex it assessed so that it doesnt break. 
        # could technically break the rules but better than a crash or halt
        self.move_robber(opp_hex, board, player)
        return

    def get_adjacent_hexes_for_player(self, board, player, exclude_selves=True):
        '''
        loop through all players and get all hexes adjacent to their settlements
        
        if exclude_selves is true, exclude any hexes that we are also adjacent to

        NOTE: did not have time to implement but using this function with exclude_selves set to false
        would be a failsafe for when we couldnt find a single spot to put the robber on
        '''
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

    def all_opponents_tied_for_vps(self):
        '''
        return true if all of our opponents have the same amount of true vps
        '''
        all_opponents = list(self.game.playerQueue.queue)
        all_opponents.remove(self)

        all_vps = [player.victoryPoints for player in all_opponents]

        prev = all_vps[0]

        for vp_score in all_vps:
            if vp_score == prev:
                prev = vp_score
                continue
            else:
                return False

        return True

    def play_knight(self, board):
        '''
        place the robber using our place robber function
        '''
        if self.devCardPlayedThisTurn:
            return

        print("{} is playing a KNIGHT...".format(self.name))

        self.place_robber(board)
        self.devCardPlayedThisTurn = True
        self.knightsPlayed += 1
        self.devCards["KNIGHT"] -= 1

        return

    def production_points_for_hex(self, board, hex_num):
        '''
        get the pp for the given hex
        '''
        return self.diceRoll_expectation[board.hexTileDict[hex_num].resource.num]

    def hex_is_adjacent_to_us(self, board, adjacent_hex):
        '''
        return true if we have a settlement adjacent to the given hex
        '''
        for settlement in self.buildGraph["SETTLEMENTS"]:
            for adj_hex in board.boardGraph[settlement].adjacentHexList:
                if adj_hex == adjacent_hex:
                    return True

        return False

    def any_settlement_blocked_by_robber(self, board):
        '''
        return true if any of our settlements have an adjacent hex blocked by the robber
        '''
        for settlement in self.buildGraph["SETTLEMENTS"]:
            for adj_hex in board.boardGraph[settlement].adjacentHexList:
                if (board.hexTileDict[adj_hex].robber == True):
                    return True
        return False

    def discard_cards(self, board):
        '''
        Function for the AI to choose a set of cards to discard upon rolling a 7

        get current goal, and discard whichever cards affect it least
        out of remaining cards, discard in order of most to least
        '''

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
        '''
        given a goal, discard one card that is in our preferred cards to discard for that goal

        if we dont have any, then discard whatever we have the most of
        '''
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

    def propose_trade(self, board, option):
        '''
        offers a trade to all other players with a specific option in mind

        requests one resource needed for the given option

        offers one resource not involved in given option

        skips if it cant offer anything or requests nothing
        '''
        debug = False

        # Select player to trade with - generate list of other players
        players = [p for p in list(self.game.playerQueue.queue)]
        players.remove(self)

        # create a trade offer
        resources_to_give, resources_to_receive = self.create_trade_offer(option)

        # if we dont ask for any, dont offer any, or have none, jsut return false
        if sum(resources_to_give.values()) == 0 or sum(resources_to_receive.values()) == 0 or sum(self.resources.values()) == 0:
            return False
        
        # create a string for printing the offered/requested resources
        offered_resources_string = ""
        requested_resources_string = ""
        for resource in resources_to_give.keys():
            give_amount = resources_to_give[resource]
            receive_amount = resources_to_receive[resource]
            if give_amount > 0:
                offered_resources_string += "{} {}, ".format(
                    give_amount, resource)
            if receive_amount > 0:
                requested_resources_string += "{} {}, ".format(
                    receive_amount, resource)
        offered_resources_string = offered_resources_string[:-2]
        requested_resources_string = requested_resources_string[:-2]

        print("{} is offering {} for {}".format(self.name, offered_resources_string, requested_resources_string))

        if debug:
            self.print_player_info()

        # offer to all players
        for other_player in players:

            # if AI
            if other_player.isAI:

                # if the player accepts the trade
                if other_player.accept_or_decline_trade(board, resources_to_give, resources_to_receive):
                    # go through the resources and make the trades
                    for resource, give_amount in resources_to_give.items():
                        receive_amount = resources_to_receive[resource]

                        self.resources[resource] -= give_amount
                        self.resources[resource] += receive_amount

                        other_player.resources[resource] += give_amount
                        other_player.resources[resource] -= receive_amount
                        print("{} successfully traded {} for {} with {}".format(
                            self.name, offered_resources_string, requested_resources_string, other_player.name))
                        return True
                else:
                    print("{} rejected trade giving {} for {}".format(
                        other_player.name, offered_resources_string, requested_resources_string))
                    continue

            else:
                # for real player:
                answer = ""

                # first check if the player has all of requested resources
                for resource, amount in resources_to_receive.items():
                    # their amount < actual amount
                    if other_player.resources[resource] < amount:
                        # auto decline if they don't have enough of any of the resources
                        answer = "N"

                # otherwise prompt user for answer
                while not (answer.upper() == "Y" or answer.upper() == "N"):
                    try:
                        other_player.print_player_info()
                        answer = input("{} offers you {} in return for {}. Do you accept? [Y/N]".format(
                            self.name, offered_resources_string, requested_resources_string))
                    except:
                        print("Please input 'Y' or 'N'")

                # if yes, make the trade
                if answer.upper() == "Y":
                    for resource, give_amount in resources_to_give.items():
                        receive_amount = resources_to_receive[resource]

                        self.resources[resource] -= give_amount
                        self.resources[resource] += receive_amount

                        other_player.resources[resource] += give_amount
                        other_player.resources[resource] -= receive_amount
                    print("{} successfully traded {} for {} with {}".format(
                        self.name, offered_resources_string, requested_resources_string, other_player.name))
                    return True
                else:
                    # rejected
                    print("{} rejected trade giving {} for {}".format(
                        other_player.name, offered_resources_string, requested_resources_string))
        return False

    def create_trade_offer(self, option):
        '''
        outputs a dict of resources with the amount offered and the amount requested to receive

        function itself ensures that there are no common resources being traded i.e. brick for brick

        request (for now 1 at most) of our desired resources for the given option and offer 1 of our givable 
        resources (resource not needed for current option)
        '''
        requesting = {'ORE': 0, 'BRICK': 0, 'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}
        offering = {'ORE': 0, 'BRICK': 0, 'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}

        # get our remaining resources needed for the option 
        resources_needed = self.get_resources_needed_for(option)
        
        # shuffle the order
        resource_list = list(resources_needed.keys())
        np.random.shuffle(resource_list)

        for resource in resource_list:
            # for our current option, request something we need
            # if we need some of this resource
            amount = resources_needed[resource]
            if amount > 0:
                # request 1 of it
                requesting[resource] = 1
                break

        # loop through our resources
        for resource, amount in self.resources.items():
            # only offer something you aren't requesting. AND only offer something you have
            if requesting[resource] == 0 and self.resources[resource] > 0:
                # consider offering 1 of this resource
                offering = {'ORE': 0, 'BRICK': 0,
                            'WHEAT': 0, 'WOOD': 0, 'SHEEP': 0}
                offering[resource] = 1

                # if we can trade this resource away without breaking current option
                if self.can_trade_without_breaking(option, offering):
                    # break and use the offer
                    break
                else:
                    # otherwise try the next resource
                    continue

        return offering, requesting

    def accept_or_decline_trade(self, board, to_receive, to_give):
        '''
        auto reject if we have no cards

        if we receive something towards our top goal

        and we dont give away anything that breaks our top 2 goals

        accept

        otherwise reject

        IMPROVEMENTS: 
        - check how MUCH it helps our hand
        - determine whether we should accept trades that would put us over 7 cards based on how many rolls until we play
        '''
        if sum(self.resources.values()) == 0 or sum(to_receive.values()) == 0 or sum(to_give.values()) == 0:
            return False

        # if we dont even have any, decline
        for resource, amount in to_give.items():
            # if we dont have enough
            if self.resources[resource] == 0 or self.resources[resource] < amount:
                return False
            
        move_goals = self.get_move_goals(board)
        options = list(move_goals.keys())
        options.sort(reverse=True, key=lambda goal: move_goals[goal])

        # if the trade hurts our top 2 goals, decline
        if not self.can_trade_without_breaking(options[0], to_give) or not self.can_trade_without_breaking(options[1], to_give):
            return False
        

        # if it is one of the resources we want
        for resource, amount in to_receive.items():
            if amount > 0:
                # if we need this resource for either of our top option, accept the trade
                if self.get_resources_needed_for(options[0])[resource] > 0:
                    return True

        return False

    def can_trade_without_breaking(self, build_option, resources_to_give):
        '''
        sloppy and quick re-use of can_build_without_breaking. instead of automatically getting the cost of the breaking option, takes in resources_to_give

        given an option and a proposed dict of resources to give, determine whether we have enough resources to do 
        the trade without going below what is needed for the build option

        return true if we can build our breaking option and we have not gone below what cards are needed for the build option
        '''
        debug = False

        # dict from option to a DICT OF RESOURCE:NUMBER representing the cost for the option
        cost_of_build_option = self.option_to_resources_required_dict[build_option]

        if debug:
            print("Checking if {} conflicts with {}".format(
                resources_to_give, build_option))

        # for each resource
        for resource in cost_of_build_option.keys():

            current_amount = self.resources[resource]
            required_amount = cost_of_build_option[resource]
            possible_breaking_amount = resources_to_give[resource]

            # if we don't need this resource for either of the build options, it doesnt matter
            # if we dont have the resource, then building anything cant decrease this below the threshold
            if required_amount == 0 or possible_breaking_amount == 0 or current_amount == 0:
                if debug:
                    print(" It does not conflict")
                continue

            if debug:
                print(" For {}, we have {} {}, we need {}, and want {} of {}".format(
                    build_option, current_amount, resource, required_amount, possible_breaking_amount, resource))
                print(" If we made the trade, we'd have {} {} remaining for {}".format(
                    current_amount-possible_breaking_amount, resource, build_option))

            # if our current amount minus the cost of the breaking option is less than what we need for our
            # build option, it would break our resources for the build optoin
            if current_amount - possible_breaking_amount < required_amount:
                if debug:
                    print(" It DOES conflict")
                return False

            if debug:
                print()
        return True
