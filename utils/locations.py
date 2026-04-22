import discord


LOCATIONS: dict[str, list[str]] = {
    "Royaume des Castherian": ["Herin", "Lympstony", "Berley", "Axbrid"],
    "Empire d'Argoratinia" : ["Stornes", "Gazd", "Lududh", "Congtonbu", "Congraring"],
    "Tribus de Torklia": ["Bale", "Malasha"],
    "Confédération des Crerish" : ["Zararaled", "Brogri", "Rordrush", "Bhic"]
}

COLOR_BY_TYPE: dict[str, discord.Color] = {
    "capital": discord.Color.dark_red(),
    "city": discord.Color.dark_blue(),
    "village": discord.Color.dark_green(),
}

CITIES_DATA: dict[str, dict[str, any]] = {
    "Bale" : {
        "type": "capital",
        "population": 11605,
        "realm": "Tribus de Torklia",
        "POIs": ["Université minérale", "Réserve naturelle"],
        "lore": "Accrochée aux hauteurs balayées par les vents marins, Bale garde les cols entre mer et continent. Les Esprits de la nature y extraient les minéraux avec respect et échangent peaux et pierres rares issues des reliefs sauvages. Entre l’Université minérale et la réserve naturelle qui entoure la cité, Bale cultive un équilibre subtil entre savoir, survie et puissance tribale."
    },
    "Herin" : {
        "type": "capital",
        "population": 7329,
        "realm": "Royaume des Castherian",
        "POIs": ["Remparts antiques", "Académies d'arts", "Place des Chroniques"],
        "lore": "Dressée sous un ciel aux hivers mordants et aux étés francs, Herin veille sur les plaines orientales derrière ses remparts antiques. Les Nains des Castherian y ont façonné une cité de granite et de feu, où la forge ancestrale résonne nuit et jour. Entre académies d’arts et ateliers d’artisans, la ville grave dans la pierre et le métal la mémoire vivante du royaume."
    },
    "Stornes" : {
        "type": "capital",
        "population": 21823,
        "realm": "Empire d'Argoratinia",
        "POIs": ["Palais Royal", "Ports fluviaux", "Quartier des Ambassades"],
        "lore": "Érigée à la rencontre des fleuves et de la mer, Stornes contrôle les routes commerciales occidentales. Ses quais bruissent de diplomates et de marchands venus de tout le continent. Le Palais Royal, dominant les eaux, symbolise la puissance navale et économique de l'Empire."
    },
    "Zararaled": {
        "type": "capital",
        "population": 2512,
        "realm": "Confédération des Crerish",
        "POIs" : ["Tours ésotériques", "Grande Bibliothèque", "Observatoire côtier"],
        "lore": "Lovée sur une côte battue par les brumes tempérées, Zararaled élève ses tours ésotériques au-dessus des flots. Les Mages blancs de la Confédération y échangent savoir et arts occultes, scrutant depuis l’observatoire côtier les astres et les marées. Dans la Grande Bibliothèque, chaque parchemin nourrit la quête d’une vérité que la mer semble murmurer sans jamais la livrer tout à fait."
    },
    "Lympstony" : {
        "type": "city",
        "population": 35095,
        "realm": "Royaume des Castherian",
        "POIs": ["Château des nains", "Grand port forgeron", "Place des Tavernes"],
        "lore": "À la lisière de la mer et d'une forêt millénaire, Lympstony est un pilier économique du royaume. Les routes s'y perdent parfois sous la canopée, et certains jurent que la forêt choisit elle-même qui peut en sortir."
    },
    "Congraring" : {
        "type": "city",
        "population": 9434,
        "realm": "Empire d'Argoratinia",
        "POIs": ["Ponts de pierre", "Quais marchands"],
        "lore": "Contrôlant l'accès aux voies navigables orientales, Congraring agit comme verrou commercial de l'Empire. Ses ponts massifs relient des quartiers construits sur des îlots naturels, animés par le va-et-vient constant des barges marchandes."
    },
    "Bhic": {
        "type": "city",
        "population": 4874,
        "realm": "Confédération des Crerish",
        "POIs": ["Vignobles en terrasses", "Marché des vendanges"],
        "lore": "Adossée à des vignobles en terrasses et ouverte sur le lac qui sépare la Confédération des Crerish de l’Empire d’Argoratinia, Bhic prospère sous un climat méditerranéen doux. Mages blancs et Elfes noirs y cultivent la vigne autant que les alliances, échangeant vin et récoltes sur les quais comme au marché des vendanges. Dans les caves creusées sous la roche, les millésimes vieillissent à l’abri des tensions frontalières, tandis que le lac reflète une paix toujours délicate."
    },
    "Brogri": {
        "type": "city",
        "population": 3546,
        "realm": "Confédération des Crerish",
        "POIs": ["Mines de cuivre", "Quartier des forges", "Observatoire alchimique"],
        "lore": "Perchée dans les montagnes battues par les vents froids venus du large, Brogri puise dans ses mines de cuivre la matière première de ses arts. Les Mages blancs y mêlent alchimie et magie minérale, transformant les métaux dans le quartier des forges en artefacts prisés. La nuit, les lueurs des ateliers et de l’observatoire alchimique constellent les sommets, comme si la montagne elle-même expérimentait avec les étoiles."
    },
    "Gazd": {
        "type": "city",
        "population": 3391,
        "realm": "Empire d'Argoratinia",
        "POIs": ["Carrefour central", "Marché nocturne"],
        "lore": "Traversée par une rivière vitale au cœur des terres arides, Gazd est le carrefour occidental de l’Empire d’Argoratinia. Ses quais et son marché nocturne accueillent caravanes et marchands d’épices avant la traversée des étendues brûlantes. Maîtres de l’eau et du commerce, les Elfes noirs y ont bâti une prospérité discrète mais stratégique."
    },
    "Berley" : {
        "type": "city",
        "population": 4466,
        "realm": "Royaume des Castherian",
        "POIs": ["Port fortifié", "Marais salants", "Tours côtières"],
        "lore": "Bâtie sur une avancée rocheuse battue par un climat marin rude, Berley dresse ses tours côtières face à l’horizon. Les Nains y ont creusé un port fortifié dans la pierre même, protégeant pêcheurs et convois de sel. Entre marais salants étincelants et quais robustes, la ville vit au rythme des marées, mêlant discipline militaire et labeur maritime."
    },
    "Rordrush": {
        "type": "city",
        "population": 20460,
        "realm": "Confédération des Crerish",
        "POIs": ["Citadelle sacrée", "Grand marché central"],
        "lore": "Au centre des plaines tempérées, Rordrush attire routes et ambitions comme un aimant de pierre blanche. Dominée par sa citadelle sacrée, la ville voit affluer caravanes, émissaires et cargaisons venues de tout le continent. Les Mages blancs y orchestrent un négoce savant, où chaque transaction au grand marché central peut devenir traité, pacte ou fragile équilibre entre Empire et Confédération."
    },
    "Axbrid" : {
        "type": "village",
        "population": 356,
        "realm": "Royaume des Castherian",
        "POIs": ["Barques de pêche", "Pâturages escarpés"],
        "lore": "Accroché à la roche au-dessus d’une mer souvent agitée, Axbrid vit entre embruns et pâturages escarpés. Les Nains y tirent poissons des eaux froides et fromages robustes des chèvres des hauteurs. Leurs barques défient les courants, tandis que les sentiers côtiers, taillés dans la pierre, protègent le village autant qu’ils forgent le caractère endurant de ses habitants."
    },
    "Congtonbu" : {
        "type": "village",
        "population": 360,
        "realm": "Empire d'Argoratinia",
        "POIs": ["Taverne des côtes hurlantes", "Port de commerce"],
        "lore": "Blotti contre des montagnes poussiéreuses, Congtonbu s’est creusé dans la roche pour échapper à la chaleur et aux vents secs. Les habitations troglodytes entourent des vestiges bien antérieurs à l’Empire d’Argoratinia, dont les pierres gravées murmurent un savoir ancien. Vivant de subsistance et de patience, les Elfes noirs y préservent ces fragments du passé comme une mémoire que le sable n’a pas su effacer."
    },
    "Lududh" : {
        "type": "village",
        "population": 1080,
        "realm": "Empire d'Argoratinia",
        "POIs": ["Clairière Hurlante"],
        "lore": "Établi sur des pentes au climat montagnard doux, Lududh vit de ses troupeaux et de ses marchés saisonniers qui relient les hauteurs aux vallées impériales. Mais au-delà des pâturages s’ouvre la Clairière Hurlante, ancien donjon à ciel ouvert dont les pierres disjointes encerclent un cœur oublié. Les soirs de pleine lune, un hurlement y résonne dans les collines, rappelant aux Elfes noirs que certaines ruines ne dorment jamais tout à fait."
    },
    "Malasha" : {
        "type": "village",
        "population": 1105,
        "realm": "Tribus de Torklia",
        "POIs": ["Champs de blé noir", "Moulin tribal"],
        "lore": "Blottie entre des reliefs protecteurs, Malasha prospère sous un climat sec rendu fertile par ses canaux d’irrigation. Les Esprits de la nature y veillent sur les champs de blé noir, dont la robustesse nourrit les tribus des hauteurs. Autour du moulin tribal, les récoltes rythment la vie du village et assurent des réserves précieuses lorsque les temps se durcissent."
    },
}