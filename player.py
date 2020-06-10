#Karan Vombatkere
#Summer 2020

#Imports
from board import *
import numpy as np

#Class definition for a player
class player():
    'Class Definition for Game Player'

    #Initialize a game player, we use A, B and C to identify
    def __init__(self, playerName, playerColor):
        self.name = playerName
        self.color = playerColor
        self.victoryPoints = 0
        self.isAI = False

        self.settlementsLeft = 5
        self.roadsLeft = 15
        self.citiesLeft = 4
        self.resources = {'ORE':10, 'BRICK':20, 'WHEAT':10, 'WOOD':20, 'SHEEP':10} #Dictionary that keeps track of resource amounts

        self.knightsPlayed = 0
        self.largestArmyFlag = False
        
        self.maxRoadLength = 0
        self.longestRoadFlag = False

        #Undirected Graph to keep track of which vertices and edges player has colonised
        #Every time a player's build graph is updated the gameBoardGraph must also be updated

        #Each of the 3 lists store vertex information - Roads are stores with tuples of vertex pairs
        self.buildGraph = {'ROADS':[], 'SETTLEMENTS':[], 'CITIES':[]} 

        #Dev cards in possession
        self.newDevCards = [] #List to keep the new dev cards draw - update the main list every turn
        self.devCards = {'KNIGHT':0, 'VP':0, 'MONOPOLY':0, 'ROADBUILDER':0, 'YEAROFPLENTY':0} 
        self.devCardPlayedThisTurn = False
        #self.visibleVictoryPoints = self.victoryPoints - devCard victory points


    #function to build a road from vertex v1 to vertex v2
    def build_road(self, v1, v2, board):
        'Update buildGraph to add a road on edge v1 - v2'

        if(self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0): #Check if player has resources available
            if(self.roadsLeft > 0): #Check if player has roads left
                self.buildGraph['ROADS'].append((v1,v2))
                self.roadsLeft -= 1

                #Update player resources
                self.resources['BRICK'] -= 1
                self.resources['WOOD'] -= 1

                board.updateBoardGraph_road(v1, v2, self) #update the overall boardGraph

                #Calculate current max road length and update
                maxRoads = self.get_road_length(board)
                self.maxRoadLength = maxRoads

                print('Player {} Built a Road. MaxRoadLength: {}'.format(self.name, self.maxRoadLength))

        else:
            print("Insufficient Resources to Build Road - Need 1 BRICK, 1 WOOD")


    #function to build a settlement on vertex with coordinates vCoord
    def build_settlement(self, vCoord, board):
        'Update player buildGraph and boardgraph to add a settlement on vertex v'
        #Take input from Player on where to build settlement
            #Check if player has correct resources
                #Update player resources and boardGraph with transaction

        if(self.resources['BRICK'] > 0 and self.resources['WOOD'] > 0 and self.resources['SHEEP'] > 0 and self.resources['WHEAT'] > 0): #Check if player has resources available
            if(self.settlementsLeft > 0): #Check if player has settlements left
                self.buildGraph['SETTLEMENTS'].append(vCoord)
                self.settlementsLeft -= 1

                #Update player resources
                self.resources['BRICK'] -= 1
                self.resources['WOOD'] -= 1
                self.resources['SHEEP'] -= 1
                self.resources['WHEAT'] -= 1
                
                self.victoryPoints += 1
                board.updateBoardGraph_settlement(vCoord, self) #update the overall boardGraph
                print('Player {} Built a Settlement'.format(self.name))
  
        else:
            print("Insufficient Resources to Build Settlement. Build Cost: 1 BRICK, 1 WOOD, 1 WHEAT, 1 SHEEP")

    #function to build a city on vertex v
    def build_city(self, vCoord, board):
        'Upgrade existing settlement to city in buildGraph'
        if(self.resources['WHEAT'] >= 2 and self.resources['ORE'] >= 3): #Check if player has resources available
            if(self.citiesLeft > 0):
                self.buildGraph['CITIES'].append(vCoord)
                self.settlementsLeft += 1 #Increase number of settlements and decrease number of cities
                self.citiesLeft -=1

                #Update player resources
                self.resources['ORE'] -= 3
                self.resources['WHEAT'] -= 2
                self.victoryPoints += 1

                board.updateBoardGraph_city(vCoord, self) #update the overall boardGraph
                print('Player {} Built a City'.format(self.name))

        else:
            print("Insufficient Resources to Build City. Build Cost: 3 ORE, 2 WHEAT")
    
    #function to move robber to a specific hex and steal from a player
    def move_robber(self, hexIndex, board, player_robbed):
        'Update boardGraph with Robber'
        board.updateBoardGraph_robber(hexIndex)
        
        #Steal a random resource from other players
        self.steal_resource(player_robbed)


    #Function to steal a random resource from player_2
    def steal_resource(self, player_2):
        if(player_2 == None):
            print("No Player on this hex to Rob")
            return
        
        #Get all resources player 2 has in a list and use random list index to steal
        p2_resources = []
        for resourceName, resourceAmount in player_2.resources.items():
            p2_resources += [resourceName]*resourceAmount

        resourceIndexToSteal = np.random.randint(0, len(p2_resources))

        #Get a random permutation and steal a card
        p2_resources = np.random.permutation(p2_resources)
        resourceStolen = p2_resources[resourceIndexToSteal]
        
        #Update resources of both players
        player_2.resources[resourceStolen] -= 1
        self.resources[resourceStolen] += 1
        print("Stole 1 {} from Player {}".format(resourceStolen, player_2.name))
        
    #Function to calculate road length for longest road calculation
    #Use both player buildgraph and board graph to compute recursively
    def get_road_length(self, board):
        roadLengths = [] #List to store road lengths from each starting edge
        for road in self.buildGraph['ROADS']: #check for every starting edge
            self.road_i_lengths = [] #List to keep track of all lengths of roads resulting from this root road
            roadCount = 0
            roadArr = []
            vertexList = []
            #print("Start road:", road)
            self.check_path_length(road, roadArr, roadCount, vertexList, board.boardGraph)

            road_inverted = (road[1], road[0])
            roadCount = 0
            roadArr = []
            vertexList = []
            self.check_path_length(road_inverted, roadArr, roadCount, vertexList, board.boardGraph)
                
            roadLengths.append(max(self.road_i_lengths)) #Update roadLength with max starting from this road
            #print(self.road_i_lengths)

        #print("Road Lengths:", roadLengths, max(roadLengths))
        return max(roadLengths)

    #Function to checl the path length from a current edge to all possible other vertices not yet visited by t
    def check_path_length(self, edge, edgeList, roadLength, vertexList, boardGraph):
        #Append current edge to list and increment road count
        edgeList.append(edge) #Append the road
        roadLength += 1
        vertexList.append(edge[0]) #Append the firs vertex
        
        #Get new neighboring forward edges from this edge - not visited by the search yet
        road_neighbors_list = self.get_neighboring_roads(edge, boardGraph, edgeList, vertexList)
        
        #print(neighboringRoads)
        #if no neighboring roads exist append the roadLength upto this edge
        if(road_neighbors_list == []):
            #print("No new neighbors found")
            self.road_i_lengths.append(roadLength)
            return

        else:
            #check paths from left and right neighbors separately
            for neighbor_road in road_neighbors_list:
                #print("checking neighboring edge:", neighbor_road)
                self.check_path_length(neighbor_road, edgeList, roadLength, vertexList, boardGraph)



    #Helper function to get neighboring edges from this road that haven't already been explored
    #We want forward neighbors only
    def get_neighboring_roads(self, road_i, boardGraph, visitedRoads, visitedVertices):
        #print("Getting neighboring roads for current road:", road_i)
        newNeighbors = []
        #Use v1 and v2 to get the vertices to expand from
        v1 = road_i[0]
        v2 = road_i[1] 
        for edge in self.buildGraph['ROADS']:
            if(edge[1] in visitedVertices):
                edge = (edge[1], edge[0]) #flip the edge if the orientation is reversed

            if(edge not in visitedRoads): #If it is a new distinct edge
                if(boardGraph[v2].state['Player'] in [self, None]):#Add condition for vertex to be not colonised by anyone else
                    if(edge[0] == v2 and edge[0] not in visitedVertices):  #If v2 has neighbors, defined starting or finishing at v2
                        #print("Appending NEW neighbor:", edge)
                        newNeighbors.append(edge)

                    if(edge[0] == v1 and edge[0] not in visitedVertices):
                        newNeighbors.append(edge)

                    if(edge[1] == v2 and edge[1] not in visitedVertices): #If v1 has neighbors, defined starting or finishing at v2
                        newNeighbors.append((edge[1], edge[0]))

                    if(edge[1] == v1 and edge[1] not in visitedVertices):
                        newNeighbors.append((edge[1], edge[0]))

        return newNeighbors

        
    #function to end turn
    def end_turn():
        'Pass turn to next player and update game state'

    #function to draw a Development Card
    def draw_devCard(self, board):
        'Draw a random dev card from stack and update self.devcards'
        if(self.resources['WHEAT'] >= 1 and self.resources['ORE'] >= 1 and self.resources['SHEEP'] >= 1): #Check if player has resources available
            #Get alldev cards available
            devCardsToDraw = []
            for cardName, cardAmount in board.devCardStack.items():
                devCardsToDraw += [cardName]*cardAmount

            #IF there are no devCards left
            if(devCardsToDraw == []):
                print("No Dev Cards Left!")
                return

            devCardIndex = np.random.randint(0, len(devCardsToDraw))

            #Get a random permutation and draw a card
            devCardsToDraw = np.random.permutation(devCardsToDraw)
            cardDrawn = devCardsToDraw[devCardIndex]

            #Update player resources
            self.resources['ORE'] -= 1
            self.resources['WHEAT'] -= 1
            self.resources['SHEEP'] -= 1

            #If card is a victory point apply immediately, else add to new card list
            if(cardDrawn == 'VP'):
                self.victoryPoints += 1
                board.devCardStack[cardDrawn] -= 1
                self.devCards[cardDrawn] += 1
            
            else:#Update player dev card and the stack
                self.newDevCards.append(cardDrawn)
                board.devCardStack[cardDrawn] -= 1
            
            print("Player {} drew a {} from Development Card Stack".format(self.name, cardDrawn))

        else:
            print("Insufficient Resources for Dev Card. Cost: 1 ORE, 1 WHEAT, 1 SHEEP")

    #Function to update dev card stack with dev cards drawn from prior turn
    def updateDevCards(self):
        for newCard in self.newDevCards:
            self.devCards[newCard] += 1

        #Reset the new card list to blank
        self.newDevCards = []

    #function to play a development card
    def play_devCard(self):
        'Update game state'
        #Check if player can play a devCard this turn
        if(self.devCardPlayedThisTurn):
            print('Already played 1 Dev Card this turn!')
            return

        #Get a list of all the unique dev cards this player can play
        devCardsAvailable = []
        for cardName, cardAmount in self.devCards.items():
            if(cardName != 'VP' and cardAmount >= 1): #Exclude Victory points
                devCardsAvailable.append((cardName, cardAmount))

        if(devCardsAvailable == []):
            print("No Development Cards available to play")
            return
        
        #Use Keyboard control to play the Dev Card
        devCard_dict = {}
        for indx, card in enumerate(devCardsAvailable):
            devCard_dict[indx] = card[0]

        print("Development Cards Available to Play", devCard_dict)

        devCardNumber = -1
        while (devCardNumber not in devCard_dict.keys()):
            devCardNumber = int(input("Enter Dev card number to play:"))

        #Play the devCard and update player's dev cards
        devCardPlayed = devCard_dict[devCardNumber]
        self.devCardPlayedThisTurn = True

        print("Playing Dev Card:", devCardPlayed)
        self.devCards[devCardPlayed] -= 1

        #TO-DO: Add functionality to play a devCard


    #function to initate a trade - with bank or other players
    def initiate_trade():
        return None