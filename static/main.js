const socket = io('http://127.0.0.1:5000/play')
$(document).ready(function() {
    var CashInStarsClicked = false;
    var AttackClicked = false;
    var ValidAttack = false;
    var TerritoryToAttack = "";
    var attackeeAttackerTroops = [];
    var reinforceFinished = false;
    var attackHappened = false;
    var MoveTroopsClicked = false;
    var TerritoryToReinforce1 = "";
    var ValidReinforcment = false;
    var ValidReinforcment2 = false;
    var ReinforceToReinforceFromTroops = [];

    $('.btnAlaska, .btnNorthwestTerritory, .btnAlberta, .btnWesternUS, .btnOntario, .btnQuebec, .btnGreenland, .btnEasternUS, .btnCentralAmerica, .btnVenezuela, .btnBrazil, .btnPeru, .btnArgentina, .btnNorthAfrica, .btnEgypt, .btnEastAfrica, .btnCongo, .btnSouthAfrica, .btnMadagascar, .btnIceland, .btnGreatBritain, .btnScandinavia, .btnNorthernEurope, .btnUkraine, .btnSouthernEurope, .btnWesternEurope, .btnIndonesia, .btnNewGuinea, .btnWesternAustralia, .btnEasternAustralia, .btnUral, .btnSiberia, .btnAfghanistan, .btnMiddleEast, .btnIndia, .btnYakutsk, .btnKamchatka, .btnChina, .btnSiam, .btnIrkutsk, .btnMongolia, .btnJapan').click(function() {
        var buttonText = $(this).attr('name');
        if (AttackClicked == true){
            socket.emit('buttonClickedAttack', {buttonText: buttonText})
        }
        else if (ValidAttack == true) {
            var TerritoryToAttackFrom = buttonText;
            ListOfTerritories = [TerritoryToAttack, TerritoryToAttackFrom];
            socket.emit('AttackFrom', {ListOfTerritories: ListOfTerritories});
            TerritoryToAttack = "";
        }
        else if (MoveTroopsClicked == true){
            socket.emit('moveTroops', {territoryToReinforce:buttonText});
        }
        else if (ValidReinforcment == true){
            reinforceReinforceFrom =[TerritoryToReinforce1, buttonText];
            socket.emit('moveTroops3', {reinforceReinforceFrom:reinforceReinforceFrom});
        }
        else {
            socket.emit('buttonClicked', { button_text: buttonText });
        }
        CashInStarsClicked = false;
    });

    
    function updateButtonText(newButtonText) {
        $('.btnAlaska, .btnNorthwestTerritory, .btnAlberta, .btnWesternUS, .btnOntario, .btnQuebec, .btnGreenland, .btnEasternUS, .btnCentralAmerica, .btnUral, .btnSiberia, .btnAfghanistan, .btnMiddleEast, .btnIndia, .btnYakutsk, .btnKamchatka, .btnChina, .btnSiam, .btnIrkutsk, .btnMongolia, .btnJapan, .btnIndonesia, .btnNewGuinea, .btnWesternAustralia, .btnEasternAustralia, .btnIceland, .btnGreatBritain, .btnScandinavia, .btnNorthernEurope, .btnUkraine, .btnSouthernEurope, .btnWesternEurope, .btnNorthAfrica, .btnEgypt, .btnEastAfrica, .btnCongo, .btnSouthAfrica, .btnMadagascar, .btnVenezuela, .btnBrazil, .btnPeru, .btnArgentina').each(function() {
            var territoryName = $(this).attr('name');
            if (newButtonText[territoryName]) {
                $(this).text(newButtonText[territoryName]);
              }
        });
    }
    
    socket.on('updateButtonText', function(data) {
        console.log('Received updateButtonText event');
        var newTerritoryName = data.button_text;
        updateButtonText(newTerritoryName);

    });

    function updateButtonColor(newButtonColor) {
        $('.btnAlaska, .btnNorthwestTerritory, .btnAlberta, .btnWesternUS, .btnOntario, .btnQuebec, .btnGreenland, .btnEasternUS, .btnCentralAmerica, .btnUral, .btnSiberia, .btnAfghanistan, .btnMiddleEast, .btnIndia, .btnYakutsk, .btnKamchatka, .btnChina, .btnSiam, .btnIrkutsk, .btnMongolia, .btnJapan, .btnIndonesia, .btnNewGuinea, .btnWesternAustralia, .btnEasternAustralia, .btnIceland, .btnGreatBritain, .btnScandinavia, .btnNorthernEurope, .btnUkraine, .btnSouthernEurope, .btnWesternEurope, .btnNorthAfrica, .btnEgypt, .btnEastAfrica, .btnCongo, .btnSouthAfrica, .btnMadagascar, .btnVenezuela, .btnBrazil, .btnPeru, .btnArgentina').each(function() {
            var territoryName = $(this).attr('name');
            if (newButtonColor[territoryName]) {
                $(this).css('color', newButtonColor[territoryName]);
            }
        })
    }

    socket.on('updateButtonColor', function(data) {
        console.log('Received updateButtonColor event');
        var newTerritoryColor = data.button_color;
        updateButtonColor(newTerritoryColor);
    })

    $('.btnAttack').click(function() {
        if (reinforceFinished == true){
            $('.textPrompt').text("Select a valid territory to attack")
            AttackClicked = true;
            CashInStarsClicked = false;
        }
    });

    $('.btnCashInStars').click(function() {
        if (attackHappened == false) {
            CashInStarsClicked = true;
            AttackClicked = false;
            $('.textPrompt').text("Select a valid number of stars to cash in")
        }
    });

    $('.btnMoveTroops').click(function() {
        if (reinforceFinished == true){
            AttackClicked = false;
            ValidAttack = false;
            MoveTroopsClicked = true;
            $('.textPrompt').text('Select a valid territory to reinforce')
            CashInStarsClicked = false;
        }
    });

    $('.btnEndTurn').click(function() {
        if (reinforceFinished == true){
            var buttonText = $(this).attr('id');
            AttackClicked = false;
            socket.emit('buttonClickedEndTurn', { button_text_move: buttonText });
            CashInStarsClicked = false;
        }
    });

    socket.on('changeTextPrompt', function(data) {
        var textThenBool = data['textBool'];
        reinforceFinished = textThenBool[1];
        console.log('hello')
        $('.textPrompt').text(textThenBool[0]);
    })

    socket.on('changeStarText', function(data){
        var starText = data['starText'];
        $('.textPrompt2').text(starText);
    })

    $('.btnStars2, .btnStars3, .btnStars4, .btnStars5, .btnStars6, .btnStars7, .btnStars8, .btnStars9, .btnStars10').click(function() {
        var starsPicked = $(this).attr('id');
        AttackClicked = false;
        console.log('hello')
        if (CashInStarsClicked == true){
            socket.emit('starsPicked', { stars: starsPicked });
            CashInStarsClicked = false;
        }
    });

    $('.btnSubmitNumTroops').click(function(){
        if (ValidAttack == true){
            var attackingWith = parseInt($('.numTroops').val());
            var attackee = attackeeAttackerTroops[0];
            var Attacker = attackeeAttackerTroops[1];
            var attackeeAttackerTroops1 = [attackee, Attacker, attackingWith];
            socket.emit('numTroopsAttacking', {attackeeAttackerTroops1:attackeeAttackerTroops1});
            $('.textPrompt').text("Beginning attack");
            attackHappened = true;
            ValidAttack = false;
        }
        if (ValidReinforcment2 == true){
            ReinforceToReinforceFromTroops[2] = parseInt($('.numTroops').val());
            socket.emit('moveTroops5', {ReinforceToReinforceFromTroops:ReinforceToReinforceFromTroops})
            $('.textPrompt').text("Reinforcement complete")
        }
    })

    socket.on('Attack', function(data){
        AttackClicked = false;
        ValidAttack = true;
        TerritoryToAttack = data['territoryAttack'];
        $('.textPrompt').text("Select a valid territory to attack from");
    })

    socket.on('attackTroops', function(data){
       attackeeAttackerTroops = data['listOfAttack'];
       $('.numTroops').attr('max', (attackeeAttackerTroops[2] - 1));
       $('.textPrompt').text("Select number of troops to attack with");
    })

    socket.on('moveTroops2', function(data){
        TerritoryToReinforce1 = data['territoryToReinforce'];
        $('.textPrompt').text("Select a valid territory to reinforce from");
        ValidReinforcment = true;
        MoveTroopsClicked = false;
    })

    socket.on('moveTroops4', function(data){
        ValidReinforcment2 = true;
        ValidAttack = false;
        ReinforceToReinforceFromTroops = data['ReinforceToReinforceFromMaxTroops']
        $('.numTroops').attr('max', (ReinforceToReinforceFromTroops[2] - 1))
        $('.textPrompt').text("Select number of troops to reinforce with")
    })

    socket.on('TurnEnded', function(data){
        texts = data['texts']
        $('.textPrompt').text(texts[0])
        $('.textPrompt2').text(texts[1])
        reinforceFinished = false;
        CashInStarsClicked = false;
        AttackClicked = false;
        ValidAttack = false;
        TerritoryToAttack = "";
        attackeeAttackerTroops = [];
        attackHappened = false;
        MoveTroopsClicked = false;
        TerritoryToReinforce1 = "";
        ValidReinforcment = false;
        ValidReinforcment2 = false;
        ReinforceToReinforceFromTroops = [];
    })
});
