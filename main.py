from flask import Flask, redirect, url_for, render_template, request, session
import random, copy, math
from flask_socketio import SocketIO

app = Flask(__name__, static_folder="static")
app.secret_key = 'risk_project'
socketio = SocketIO(app, async_mode = 'eventlet')

reinforceAtBegin = True
turnIndex = 0
playerList = []
players = 0
soldiersLeft = 0
soldiersCachedIn = 0
RiskGraph = {}
gainedTerritory = False
movedTroops = False

class Territory:
    def __init__(self, name_in, troops_in):
        self.name = name_in
        self.troops = troops_in
        self.player = 100000
    
    def __str__(self):
        return self.name
    
    def updateButtonText(self):
        button_text = {self.name: f"{self.name} ({self.troops})"}
        socketio.emit('updateButtonText', {'button_text':button_text}, namespace= '/play')


    def updateButtonColor(self):
        if self.player == 1:
            button_color = {self.name:'red'}
        elif self.player == 2:
            button_color = {self.name:'springgreen'}
        elif self.player == 3:
            button_color = {self.name:'yellow'}
        elif self.player == 4:
            button_color = {self.name:'deepskyblue'}
        elif self.player == 5:
            button_color = {self.name:'gray'}
        else:
            button_color = {self.name:'pink'}
        socketio.emit('updateButtonColor', {'button_color':button_color}, namespace= '/play')
    
    def get_troops(self):
        return self.troops

    def set_troops(self, newTroops):
        self.troops = newTroops
        self.updateButtonText()
    
    def set_player(self, playerIndex):
        self.player = playerIndex
        self.updateButtonColor()
    

    
class Player:
    def __init__(self, name_in):
        self.name = name_in
        self.territories = []
        self.stars = 0

def choose_territories_1_player(RiskGraphCopy, numTerritories):
    RiskDict = list(RiskGraphCopy.items()) 
    RiskDict_chosen_list = random.sample(RiskDict, numTerritories)
    RiskChosenTerritories = dict(RiskDict_chosen_list)
    return RiskChosenTerritories

def create_new_dict(RiskGraph, playersTerritories):
    remainingRiskGraph = {k: RiskGraph[k] for k in RiskGraph if k not in playersTerritories}
    return remainingRiskGraph

@socketio.on('connect', namespace='/play')
def handle_connect():
    playRisk()

@socketio.on('buttonClicked', namespace='/play')
def handle_button_clicked(data):
    global soldiersLeft
    global reinforceAtBegin
    global soldiersCachedIn
    global turnIndex
    global playerList
    territoryName = data['button_text']
    activePlayer = playerList[turnIndex]
    if soldiersLeft != 0:
        for territory in activePlayer.territories:
            if territoryName == territory.name:
                territory.set_troops(territory.get_troops() + 1)
                endTurn()
                starText = f"You have {playerList[turnIndex].stars} stars"
                socketio.emit('changeStarText', {'starText': starText}, namespace = '/play')
                soldiersLeft -= 1
                if soldiersLeft != 0:
                    text = f"Player {turnIndex + 1} place a troop"
                    doneReinforcing = False
                else:
                    doneReinforcing = True
                    text = f"Player {turnIndex + 1} place {soldiersCachedIn} troops"
                textThenBool = [text, doneReinforcing]
                socketio.emit('changeTextPrompt', {'textBool': textThenBool}, namespace = '/play')
    
    elif soldiersCachedIn != 0:
        for territory in activePlayer.territories:
            if territoryName == territory.name:
                territory.set_troops(territory.get_troops() + 1)
                soldiersCachedIn -= 1
                if soldiersCachedIn != 0:
                    reinforceDone = False
                    text = f"Player {turnIndex + 1} place {soldiersCachedIn} troops"
                else:
                    text = f"Player {turnIndex + 1} make a move"
                    reinforceDone = True
                textThenBool = [text, reinforceDone]
                socketio.emit('changeTextPrompt', {'textBool': textThenBool}, namespace = '/play')
    
    else:
        reinforceAtBegin = False

@socketio.on('AttackFrom', namespace='/play')
def handle_attack_from(data):
    global turnIndex
    global playerList
    
    activePlayer = playerList[turnIndex]
    twoTerritories = data['ListOfTerritories']
    connectedTo1 = False
    connectedTo2 = False
    keyToAccess = None
    
    for territory in activePlayer.territories:
        if territory.name == twoTerritories[1]:
            connectedTo1 = True
            keyToAccess = territory
    
    for territory1 in activePlayer.territories[keyToAccess]:
        if territory1.name == twoTerritories[0]:
            connectedTo2 = True
    
    if connectedTo1 and connectedTo2:
        if keyToAccess.troops > 1:
            maxAttackTroops = keyToAccess.troops
            nameAttacker = twoTerritories[1]
            nameAttackee = twoTerritories[0]
            attackeeAttackerTroops = [nameAttackee, nameAttacker, maxAttackTroops]
            socketio.emit('attackTroops', {'listOfAttack':attackeeAttackerTroops}, namespace='/play')
    
@socketio.on('buttonClickedAttack', namespace='/play')
def handle_button_attack_clicked(data):
    global turnIndex
    global playerList
    global gainedTerritory
    
    validToAttack = True
    activePlayer = playerList[turnIndex]
    territoryToAttack = data['buttonText']
    
    for territory in activePlayer.territories:
        if territory.name == territoryToAttack:
            validToAttack = False
    inValues = False
    print()
    for territoryLists in activePlayer.territories.values():
        for territoryValue in territoryLists:
            if territoryValue.name == territoryToAttack:
                inValues = True
    
    if inValues == False:
        validToAttack = False
    
    if validToAttack == True:
        socketio.emit('Attack', {'territoryAttack':territoryToAttack}, namespace='/play')
    

@socketio.on('moveTroops', namespace='/play')
def handle_button_move_clicked(data):
    global movedTroops
    global turnIndex
    global playerList
    global soldiersLeft
    global soldiersCachedIn
    activePlayer = playerList[turnIndex]
    territoryToReinforce = data['territoryToReinforce']
    if soldiersCachedIn == 0 and soldiersLeft == 0 and movedTroops == False:
        print('testing')
        for territory in activePlayer.territories:
                if territory.name == territoryToReinforce:
                    socketio.emit('moveTroops2', {'territoryToReinforce': territoryToReinforce}, namespace='/play')
                    print('test')

@socketio.on('moveTroops3', namespace='/play')
def check_validity_of_reinforcement(data):
    global turnIndex
    global playerList
    global RiskGraph
    activePlayer = playerList[turnIndex]
    valid = False
    reinforceReinforceFrom = data['reinforceReinforceFrom']
    territoryToReinforceFrom = None
    territoryToReinforce = None
    for territory in activePlayer.territories:
        if territory.name == reinforceReinforceFrom[1]:
            territoryToReinforceFrom = territory
            valid = True
        if territory.name == reinforceReinforceFrom[0]:
            territoryToReinforce = territory
    if territoryToReinforceFrom.troops < 2:
        valid = False
    if not find_path(activePlayer.territories, territoryToReinforceFrom, territoryToReinforce, path=[]):
        valid = False
    if valid == True:
        ReinforceToReinforceFromMaxTroops = [reinforceReinforceFrom[0], reinforceReinforceFrom[1], territoryToReinforceFrom.troops]   
        socketio.emit('moveTroops4', {'ReinforceToReinforceFromMaxTroops':ReinforceToReinforceFromMaxTroops}, namespace='/play')

@socketio.on('moveTroops5', namespace='/play')
def reinforce(data):
    global turnIndex
    global playerList
    global movedTroops
    activePlayer = playerList[turnIndex]
    ReinforceToReinforceFromTroops = data['ReinforceToReinforceFromTroops']
    territoryToReinforceFrom = None
    territoryToReinforce = None
    for territory in activePlayer.territories:
        if territory.name == ReinforceToReinforceFromTroops[1]:
            territoryToReinforceFrom = territory
        if territory.name == ReinforceToReinforceFromTroops[0]:
            territoryToReinforce = territory
    territoryToReinforceFrom.set_troops(territoryToReinforceFrom.troops - ReinforceToReinforceFromTroops[2])
    territoryToReinforce.set_troops(territoryToReinforceFrom.troops + ReinforceToReinforceFromTroops[2])
    movedTroops = True
    
@socketio.on('buttonClickedEndTurn', namespace='/play')
def handle_button_move_clicked(data):
    global turnIndex
    global playerList
    global soldiersCachedIn
    global gainedTerritory
    global movedTroops
    stillPlaying = 0
    activePlayerName = ""
    if gainedTerritory == True:
        playerList[turnIndex].stars += random.choices([1, 2], weights=[2, 1], k=1)[0]
    for player in playerList:
        if len(player.territories) != 0:
            stillPlaying += 1
            activePlayerName = player.name
    if stillPlaying == 1:
        redirect(url_for("gameover", winner = activePlayerName))
        print(f"Player {activePlayerName} wins the game")
    else:
        endTurn()
    if len(playerList[turnIndex].territories) == 0:
        while len(playerList[turnIndex].territories) == 0:
            endTurn()
    
    soldiersCachedIn = troopBonus()
    gainedTerritory = False
    movedTroops = False
    text = f"Player {turnIndex + 1} place {soldiersCachedIn} troops"
    text1 = f"You have {playerList[turnIndex].stars} stars"
    texts = [text, text1]
    socketio.emit('TurnEnded', {'texts': texts}, namespace='/play')
    
    
@socketio.on('starsPicked', namespace='/play')
def cashStars(data):
    global soldiersCachedIn
    numStars = int(data['stars'])
    if numStars <= playerList[turnIndex].stars :
        playerList[turnIndex].stars -= numStars
        if numStars == 2:
            soldiersCachedIn = 2
        elif numStars == 3:
            soldiersCachedIn = 4
        elif numStars == 4:
            soldiersCachedIn = 7
        elif numStars == 5:
            soldiersCachedIn = 10
        elif numStars == 6:
            soldiersCachedIn = 13
        elif numStars == 7:
            soldiersCachedIn = 17
        elif numStars == 8:
            soldiersCachedIn = 21
        elif numStars == 9:
            soldiersCachedIn = 25
        else:
            soldiersCachedIn = 30
        text = f"Player {turnIndex + 1} place {soldiersCachedIn} troops"
        doneReinforcing = True
        textThenBool = [text, doneReinforcing]
        socketio.emit('changeTextPrompt', {'textBool': textThenBool}, namespace = '/play')
        
        
        starText = f"You have {playerList[turnIndex].stars} stars"
        socketio.emit('changeStarText', {'starText': starText}, namespace = '/play')
        
            

@socketio.on('numTroopsAttacking', namespace='/play')
def carryOutAttack(data):
    global turnIndex
    global playerList
    global RiskGraph
    activePlayer = playerList[turnIndex]
    attackeeAttackerAndTroops = data['attackeeAttackerTroops1']
    attackerTerritory = None
    attackeePlayer = None
   
    for territory in activePlayer.territories:
        if territory.name == attackeeAttackerAndTroops[1]:
            attackerTerritory = territory
   
    for territory1 in RiskGraph:
        if territory1.name == attackeeAttackerAndTroops[0]:
            attackeeTerritory = territory1
            attackeePlayer = playerList[attackeeTerritory.player - 1]
            for territory2 in attackeePlayer.territories:
                if territory2.name == attackeeAttackerAndTroops[0]:
                    attackeeTerritory = territory2
   
    if attackeeTerritory != None:
        rollDice(attackerTerritory, attackeeTerritory, attackeeAttackerAndTroops[2])

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        session['numPlayers'] = request.form['numPlayers']
        return redirect(url_for("play"))
    else:
        return render_template("home.html")

@app.route("/play", methods=["POST", "GET"])
def play():
    
    rendered_template = render_template("play.html")
    return rendered_template

@app.route("/gameover")
def gameover(winner):
    return render_template("gameover.html", content = winner)

def rollDice(attacker, attackee, troops):
    global turnIndex
    global playerList
    global gainedTerritory
    
    attackedPlayer = playerList[attackee.player - 1]
    activePlayer = playerList[turnIndex]
    attacker.set_troops(attacker.troops - troops) 
    
    while troops > 0 and attackee.troops > 0:
        diceAttacker = []
        diceAttackee = []
        die1Attacker = random.randint(1,6)
        diceAttacker.append(die1Attacker)
       
        if troops > 1:
            die2Attacker = random.randint(1,6)
            diceAttacker.append(die2Attacker)
        if troops >= 3:
            die3Attacker = random.randint(1,6)
            diceAttacker.append(die3Attacker)
        
        die1Attackee = random.randint(1,6)
        diceAttackee.append(die1Attackee)
        
        if attackee.troops > 1:
            die2Attackee = random.randint(1,6)
            diceAttackee.append(die2Attackee)
        
        diceAttacker.sort()
        diceAttackee.sort()
        
        if len(diceAttacker) < len(diceAttackee):
            for i in range(len(diceAttacker)):
                if diceAttacker[len(diceAttacker) - 1 - i] > diceAttackee[len(diceAttackee) - 1 - i]:
                    attackee.troops -= 1
                else:
                    troops -= 1
        else:
            for i in range(len(diceAttackee)):
                if diceAttacker[len(diceAttacker) - 1 - i] > diceAttackee[len(diceAttackee) - 1 - i]:
                    attackee.troops -= 1
                else:
                    troops -= 1
    if attackee.troops == 0:
        attackee.set_troops(troops)
        activePlayer.territories[attackee] = attackedPlayer.territories[attackee]
        attackedPlayer.territories.pop(attackee)
        attackee.set_player(turnIndex + 1)
        gainedTerritory = True


def find_path(graph, start, end, path=[]):
        path = path + [start]
        if start == end:
            return True
        if start not in graph:
            return False
        for node in graph[start]:
            if node not in path:
                newpath = find_path(graph, node, end, path)
                if newpath: return True
        return False
        

def endTurn():
    global turnIndex
    if turnIndex == players - 1:
        turnIndex = 0
    else:
        turnIndex += 1

def troopBonus():
    global turnIndex
    global playerList
    activePlayer = playerList[turnIndex]
    bonusTroops = 3
    NorthAmerica = 0
    SouthAmerica = 0
    Africa = 0
    Europe = 0
    Asia = 0
    Australia = 0
    numTerritories = 0
    
    for territory in activePlayer.territories:
        numTerritories += 1
        if territory.name == "Alaska":
            NorthAmerica += 1
        elif territory.name == "Northwest Territory":
            NorthAmerica += 1
        elif territory.name == "Alberta":
            NorthAmerica += 1
        elif territory.name == "Ontario":
            NorthAmerica += 1
        elif territory.name == "Greenland":
            NorthAmerica += 1
        elif territory.name == "Western U.S.":
            NorthAmerica += 1
        elif territory.name == "Eastern U.S.":
            NorthAmerica += 1
        elif territory.name == "Central America":
            NorthAmerica += 1
        elif territory.name == "Quebec":
            NorthAmerica += 1
        
        elif territory.name == "Venezuela":
            SouthAmerica += 1
        elif territory.name == "Peru":
            SouthAmerica += 1
        elif territory.name == "Brazil":
            SouthAmerica += 1
        elif territory.name == "Argentina":
            SouthAmerica += 1
        
        elif territory.name == "Iceland":
            Europe += 1
        elif territory.name == "Great Britain":
            Europe += 1
        elif territory.name == "Scandinavia":
            Europe += 1
        elif territory.name == "Northern Europe":
            Europe += 1
        elif territory.name == "Ukraine":
            Europe += 1
        elif territory.name == "Western Europe":
            Europe += 1
        elif territory.name == "Southern Europe":
            Europe += 1
        
        elif territory.name == "North Africa":
            Africa += 1
        elif territory.name == "Egypt":
            Africa += 1
        elif territory.name == "East Africa":
            Africa += 1
        elif territory.name == "Congo":
            Africa += 1
        elif territory.name == "South Africa":
            Africa += 1
        elif territory.name == "Madagascar":
            Africa += 1
        
        elif territory.name == "Ural":
            Asia += 1
        elif territory.name == "Siberia":
            Asia += 1
        elif territory.name == "Yakutsk":
            Asia += 1
        elif territory.name == "Kamchatka":
            Asia += 1
        elif territory.name == "Irkutsk":
            Asia += 1
        elif territory.name == "Afghanistan":
            Asia += 1
        elif territory.name == "Mongolia":
            Asia += 1
        elif territory.name == "Japn":
            Asia += 1
        elif territory.name == "China":
            Asia += 1
        elif territory.name == "Middle East":
            Asia += 1
        elif territory.name == "India":
            Asia += 1
        elif territory.name == "Siam":
            Asia += 1
        
        elif territory.name == "Indonesia":
            Australia += 1
        elif territory.name == "New Guinea":
            Australia += 1
        elif territory.name == "Western Australia":
            Australia += 1
        else:
            Australia += 1
        
    if NorthAmerica == 9:
        bonusTroops += 5
    if SouthAmerica == 4:
        bonusTroops += 2
    if Europe == 7:
        bonusTroops += 5
    if Africa == 6:
        bonusTroops += 3
    if Asia == 12:
        bonusTroops += 7
    if Australia == 4:
        bonusTroops += 2
    
    if numTerritories > 39:
        bonusTropps += 10
    elif numTerritories > 35:
        bonusTroops += 9
    elif numTerritories > 32:
        bonusTroops += 8
    elif numTerritories > 29:
        bonusTroops += 7
    elif numTerritories > 26:
        bonusTroops += 6
    elif numTerritories > 23:
        bonusTroops += 5
    elif numTerritories > 20:
        bonusTroops += 4
    elif numTerritories > 17:
        bonusTroops += 3
    elif numTerritories > 14:
        bonusTroops += 2
    elif numTerritories > 11:
        bonusTroops += 1
    else:
        bonusTroops += 0
        
    return bonusTroops
        
            

def playRisk():
    global turnIndex
    global soldiersLeft
    global players
    global RiskGraph
    global soldiersCachedIn
    players = int(session.get('numPlayers'))
    global playerList
    playerList = []
    
    for i in range(players):
        x = i + 1
        playerList.append(Player(x))
    
    Alaska = Territory("Alaska", 0)
    NorthwestTerritory = Territory("Northwest Territory", 0)
    Alberta = Territory("Alberta", 0)
    Ontario = Territory("Ontario", 0)
    Quebec = Territory("Quebec", 0)
    Greenland = Territory("Greenland", 0)
    WesternUS = Territory("Western U.S.", 0)
    EasternUS = Territory("Eastern U.S.", 0)
    CentralAmerica = Territory("Central America", 0)
    
    Venezuela = Territory("Venezuela", 0)
    Peru = Territory("Peru", 0)
    Brazil = Territory("Brazil", 0)
    Argentina = Territory("Argentina", 0)
    
    Iceland = Territory("Iceland", 0)
    GreatBritain = Territory("Great Britain", 0)
    Scandinavia = Territory("Scandinavia", 0)
    NorthernEurope = Territory("Northern Europe", 0)
    Ukraine = Territory("Ukraine", 0)
    WesternEurope = Territory("Western Europe", 0)
    SouthernEurope = Territory("Southern Europe", 0)
    
    NorthAfrica = Territory("North Africa", 0)
    Egypt = Territory("Egypt", 0)
    EastAfrica = Territory("East Africa", 0)
    Congo = Territory("Congo", 0)
    SouthAfrica = Territory("South Africa", 0)
    Madagascar = Territory("Madagascar", 0)
    
    Ural = Territory("Ural", 0)
    Siberia = Territory("Siberia", 0)
    Yakutsk = Territory("Yakutsk", 0)
    Kamchatka = Territory("Kamchatka", 0)
    Irkutsk = Territory("Irkutsk", 0)
    Afghanistan = Territory("Afghanistan", 0)
    Mongolia = Territory("Mongolia", 0)
    Japan = Territory("Japan", 0)
    China = Territory("China", 0)
    MiddleEast = Territory("Middle East", 0)
    India = Territory("India", 0)
    Siam = Territory("Siam", 0)
    
    Indonesia = Territory("Indonesia", 0)
    NewGuinea = Territory("New Guinea", 0)
    WesternAustralia = Territory("Western Australia", 0)
    EasternAustralia = Territory("Eastern Australia", 0)
    
    RiskGraph = {Alaska: [NorthwestTerritory, Alberta, Kamchatka],
                 NorthwestTerritory: [Alaska, Alberta, Ontario, Greenland],
                 Alberta: [Alaska, NorthwestTerritory, Ontario, WesternUS],
                 Ontario: [Alberta, NorthwestTerritory, Quebec, Greenland, EasternUS, WesternUS],
                 Quebec: [Ontario, Greenland, EasternUS],
                 Greenland: [NorthwestTerritory, Ontario, Quebec, Iceland],
                 WesternUS: [Alberta, Ontario, EasternUS, CentralAmerica],
                 EasternUS: [WesternUS, CentralAmerica, Ontario, Quebec],
                 CentralAmerica: [WesternUS, EasternUS, Venezuela],
                 Venezuela: [CentralAmerica, Peru, Brazil],
                 Peru: [Venezuela, Brazil, Argentina],
                 Brazil: [Venezuela, Peru, Argentina],
                 Argentina: [Peru, Brazil],
                 NorthAfrica: [Brazil, Egypt, WesternEurope, SouthernEurope, EastAfrica, Congo],
                 Egypt: [NorthAfrica, SouthernEurope, MiddleEast, EastAfrica],
                 EastAfrica: [Egypt, NorthAfrica, MiddleEast, Madagascar, Congo, SouthAfrica],
                 Congo: [NorthAfrica, EastAfrica, SouthAfrica],
                 SouthAfrica: [Congo, EastAfrica, Madagascar],
                 Madagascar: [SouthAfrica, EastAfrica],
                 MiddleEast: [Egypt, EastAfrica, SouthernEurope, Ukraine, Afghanistan, India],
                 India: [MiddleEast, Afghanistan, China, Siam],
                 Siam: [India, China, Indonesia],
                 China: [India, Siam, Afghanistan, Siberia, Mongolia, Ural],
                 Afghanistan: [Ukraine, Ural, China, India, MiddleEast],
                 Ural: [Ukraine, Afghanistan, China, Siberia],
                 Siberia: [Ural, China, Mongolia, Irkutsk, Yakutsk],
                 Mongolia: [China, Siberia, Irkutsk, Japan, Kamchatka],
                 Irkutsk: [Siberia, Mongolia, Yakutsk, Kamchatka],
                 Yakutsk: [Siberia, Irkutsk, Kamchatka],
                 Kamchatka: [Yakutsk, Irkutsk, Mongolia, Japan, Alaska],
                 Japan: [Kamchatka, Mongolia],
                 Indonesia: [Siam, NewGuinea, WesternAustralia],
                 NewGuinea: [Indonesia, EasternAustralia, WesternAustralia],
                 WesternAustralia: [Indonesia, NewGuinea, EasternAustralia],
                 EasternAustralia: [NewGuinea, WesternAustralia],
                 Iceland: [Greenland, GreatBritain, Scandinavia],
                 GreatBritain: [Iceland, Scandinavia, NorthernEurope, WesternEurope],
                 Scandinavia: [Iceland, GreatBritain, NorthernEurope, Ukraine],
                 NorthernEurope: [Scandinavia, Ukraine, SouthernEurope, WesternEurope, GreatBritain],
                 Ukraine: [Scandinavia, NorthernEurope, SouthernEurope, Ural, Afghanistan, MiddleEast],
                 WesternEurope: [GreatBritain, NorthernEurope, SouthernEurope, NorthAfrica],
                 SouthernEurope: [WesternEurope, NorthernEurope, Ukraine, MiddleEast, Egypt, NorthAfrica]}
    
    
    RiskGraphCopy = copy.copy(RiskGraph)
    
    if players == 2:
        playerList[0].territories = choose_territories_1_player(RiskGraphCopy, 21)
        playerList[1].territories = create_new_dict(RiskGraphCopy, playerList[0].territories)
        for territory in playerList[0].territories :
            territory.set_player(1)
        for territory1 in playerList[1].territories :
            territory1.set_player(2)
    elif players == 3:
        turnIndex = 0
        soldiersLeft = 63
        playerList[0].territories = choose_territories_1_player(RiskGraphCopy, 14)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[0].territories)
        playerList[1].territories = choose_territories_1_player(RiskGraphCopy, 14)
        playerList[2].territories = create_new_dict(RiskGraphCopy, playerList[1].territories)
        for territory in playerList[0].territories :
            territory.set_player(1)
        for territory1 in playerList[1].territories :
            territory1.set_player(2)
        for territory2 in playerList[2].territories :
            territory2.set_player(3)
    
    elif players == 4:
        turnIndex = 2
        soldiersLeft = 78
        playerList[0].territories = choose_territories_1_player(RiskGraphCopy, 11)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[0].territories)
        playerList[1].territories = choose_territories_1_player(RiskGraphCopy, 11)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[1].territories)
        playerList[2].territories = choose_territories_1_player(RiskGraphCopy, 10)
        playerList[3].territories = create_new_dict(RiskGraphCopy, playerList[2].territories)
        for territory in playerList[0].territories :
            territory.set_player(1)
        for territory1 in playerList[1].territories :
            territory1.set_player(2)
        for territory2 in playerList[2].territories :
            territory2.set_player(3)
        for territory3 in playerList[3].territories :
            territory3.set_player(4)
        
    elif players == 5:
        turnIndex = 2
        soldiersLeft = 83
        playerList[0].territories = choose_territories_1_player(RiskGraphCopy, 9)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[0].territories)
        playerList[1].territories = choose_territories_1_player(RiskGraphCopy, 9)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[1].territories)
        playerList[2].territories = choose_territories_1_player(RiskGraphCopy, 8)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[2].territories)
        playerList[3].territories = choose_territories_1_player(RiskGraphCopy, 8)
        playerList[4].territories = create_new_dict(RiskGraphCopy, playerList[3].territories)
        for territory in playerList[0].territories :
            territory.set_player(1)
        for territory1 in playerList[1].territories :
            territory1.set_player(2)
        for territory2 in playerList[2].territories :
            territory2.set_player(3)
        for territory3 in playerList[3].territories :
            territory3.set_player(4)
        for territory4 in playerList[4].territories :
            territory4.set_player(5)
    
    else :
        turnIndex = 0
        soldiersLeft = 78
        playerList[0].territories = choose_territories_1_player(RiskGraphCopy, 7)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[0].territories)
        playerList[1].territories = choose_territories_1_player(RiskGraphCopy, 7)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[1].territories)
        playerList[2].territories = choose_territories_1_player(RiskGraphCopy, 7)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[2].territories)
        playerList[3].territories = choose_territories_1_player(RiskGraphCopy, 7)
        RiskGraphCopy = create_new_dict(RiskGraphCopy, playerList[3].territories)
        playerList[4].territories = choose_territories_1_player(RiskGraphCopy, 7)
        playerList[5].territories = create_new_dict(RiskGraphCopy, playerList[4].territories)
        for territory in playerList[0].territories :
            territory.set_player(1)
        for territory1 in playerList[1].territories :
            territory1.set_player(2)
        for territory2 in playerList[2].territories :
            territory2.set_player(3)
        for territory3 in playerList[3].territories :
            territory3.set_player(4)
        for territory4 in playerList[4].territories :
            territory4.set_player(5)
        for territory5 in playerList[5].territories :
            territory5.set_player(6)
        
    
    for territory in RiskGraph:
        territory.set_troops(1)

    soldiersCachedIn = troopBonus()
    
    text = f"Player {turnIndex + 1} place a troop"
    reinforceDone = False
    textThenBool = [text, reinforceDone]
    socketio.emit('changeTextPrompt', {'textBool': textThenBool}, namespace = '/play')
    
    starText = f"You have {playerList[turnIndex].stars} stars"
    socketio.emit('changeStarText', {'starText': starText}, namespace = '/play')
                    
if __name__ == "__main__":
    socketio.run(app, debug=True)

