import discord 
# ---------------- POWER USAGE PHRASES -------------------

POWER_USE_PHRASES: dict[str, list[str]] = {
    "attaque": [
        "{character} puise dans ses réserves et déclenche **{power}**.",
        "D'un geste précis, {character} libère **{power}**.",
        "{character} frappe — **{power}** s'abat sur sa cible.",
    ],
    "attaque_furtive": [
        "{character} agit dans l'ombre et déclenche **{power}**.",
        "Silencieux·se, {character} saisit l'instant et active **{power}**.",
        "Avant même qu'on le·la remarque, {character} utilise **{power}**.",
    ],
    "attaque_magique": [
        "{character} canalise son énergie et projette **{power}**.",
        "Un murmure, un geste — **{power}** jaillit des mains {de_character}.",
        "{character} libère **{power}** dans un éclat élémentaire.",
    ],
    "defense": [
        "{character} se prépare à encaisser et active **{power}**.",
        "En réponse, {character} déclenche **{power}** pour se protéger.",
        "{character} adopte une posture et laisse **{power}** faire le reste.",
    ],
    "soin": [
        "{character} pose les mains et active **{power}**.",
        "Avec soin, {character} canalise **{power}** sur sa cible.",
        "Un geste doux mais précis — {character} utilise **{power}**.",
    ],
    "invocation": [
        "{character} fait appel à une présence extérieure via **{power}**.",
        "L'appel {de_character} résonne — **{power}** répond.",
        "{character} n'est plus seul·e : **{power}** entre en jeu.",
    ],
    "poison": [
        "{character} prépare quelque chose de discret et d'efficace : **{power}**.",
        "Un geste anodin, une conséquence fatale — {character} active **{power}**.",
        "{character} glisse **{power}** dans la mêlée sans un mot.",
    ],
    "utilitaire": [
        "{character} fait appel à **{power}** avec discrétion.",
        "Sans attirer l'attention, {character} active **{power}**.",
        "{character} sait quand utiliser **{power}** — et c'est maintenant.",
    ],
    "communication": [
        "{character} tend l'oreille et invoque **{power}**.",
        "Un échange silencieux s'amorce — {character} utilise **{power}**.",
        "{character} cherche une information et active **{power}**.",
    ],
}

POWER_USE_PHRASES_DEFAULT: list[str] = [
    "{character} utilise **{power}**.",
    "{character} active **{power}**.",
    "{character} déclenche **{power}**.",
]


# ------------------- BUFF DESCRIPTIONS -------------------
DEFAULT_BUFF_SOURCES = {
    "hp": [
        "La Bénédiction des Anciens",
        "Un souffle de vie mystérieux",
        "La grâce de Géheu",
    ],
    "mana": [
        "Les flux arcaniques de Géheu",
        "Un écho des plans éthérés",
        "La volonté des Tisserands",
    ],
    "stamina": [
        "L'ardeur du combat",
        "Un vent de volonté",
        "La fureur des Forges",
    ],
    "attaque": [
        "La rage des Conquérants",
        "Un instinct aiguisé par le sang",
        "La bénédiction des Lames",
    ],
    "défense": [
        "Le bouclier des Anciens Remparts",
        "Une peau d'acier forgée par l'épreuve",
        "La protection des Gardiens de Géheu",
    ],
    "force": [
        "La puissance des Titans endormis",
        "Un éveil musculaire inexpliqué",
        "Le don des Forges Primordiales",
    ],
    "résistance": [
        "La ténacité des Survivants",
        "Une endurance née de la douleur",
        "Le pacte des Corps Indestructibles",
    ],
    "perception": [
        "L'œil des Éclaireurs de l'Aube",
        "Un sens aiguisé par l'ombre",
        "Le don de clairvoyance des Oracles",
    ],
    "discrétion": [
        "Le voile des Ombres Errantes",
        "Un pas feutré béni par la nuit",
        "L'art des Fantômes de Géheu",
    ],
    "infiltration": [
        "Le secret des Masques Brisés",
        "Une ruse héritée des Espions du Roi",
        "Le don des Serpents de l'Ombre",
    ],
    "agilité": [
        "La grâce des Danseurs du Vent",
        "Un réflexe né des étoiles filantes",
        "La bénédiction des Acrobates Célestes",
    ],
    "default": [
        "Une force inconnue",
        "Le Destin",
        "Les Dieux de Géheu",
    ],
}

DEFAULT_BUFF_DESCRIPTIONS = {
    "hp": [
        "Une chaleur bienfaisante parcourt le corps {de_character}, restaurant sa vitalité.",
        "Les blessures {de_character} semblent se refermer sous une lumière douce.",
        "Un souffle de vie mystérieux redonne des forces à {character}.",
    ],
    "mana": [
        "Les flux arcaniques s'intensifient autour {de_character}.",
        "Une énergie éthérée irrigue l'esprit {de_character}.",
        "Les Tisserands semblent guider la magie à travers {character}.",
    ],
    "stamina": [
        "Les muscles {de_character} se tendent, prêts pour l'effort.",
        "Une énergie brute et farouche s'empare {de_character}.",
        "Le souffle {de_character} se stabilise, portée par une volonté de fer.",
    ],
    "attaque": [
        "Les gestes {de_character} deviennent plus précis, plus mortels.",
        "Une rage froide aiguise les instincts {de_character}.",
        "La lame {de_character} semble danser d'elle-même.",
    ],
    "défense": [
        "Une aura protectrice enveloppe {character}.",
        "Les coups semblent glisser sur {character} comme sur de l'acier poli.",
        "Les Gardiens de Géheu veillent sur {character}.",
    ],
    "force": [
        "Les veines {de_character} pulsent d'une énergie primitive.",
        "Une puissance titanesque s'éveille dans les membres {de_character}.",
        "Chaque mouvement {de_character} porte le poids des Forges Primordiales.",
    ],
    "résistance": [
        "La douleur semble glisser sur {character} sans laisser de trace.",
        "Le corps {de_character} s'endurcit, forgé par l'épreuve.",
        "Rien ne semble pouvoir briser {character} aujourd'hui.",
    ],
    "perception": [
        "Les sens {de_character} s'aiguisent, captant le moindre détail.",
        "Rien n'échappe au regard {de_character}.",
        "Les Oracles semblent prêter leur clairvoyance à {character}.",
    ],
    "discrétion": [
        "Les pas {de_character} deviennent silencieux comme la nuit.",
        "L'ombre semble accueillir {character} comme l'une des siennes.",
        "Les Fantômes de Géheu guident {character} dans l'obscurité.",
    ],
    "infiltration": [
        "Le masque {de_character} devient impénétrable.",
        "Chaque geste {de_character} trahit une ruse héritée des Espions du Roi.",
        "Les Serpents de l'Ombre murmurent leurs secrets à {character}.",
    ],
    "agilité": [
        "{character} se déplace comme le vent, insaisissable.",
        "Les réflexes {de_character} défient toute logique.",
        "La grâce des Danseurs du Vent habite chaque mouvement {de_character}.",
    ],
    "default": [
        "Une force mystérieuse s'empare {de_character}.",
        "Le Destin semble agir à travers {character}.",
        "Les Dieux de Géheu posent leur regard sur {character}.",
    ],
}

# ------------------- CRAFT OUTCOMES -------------------

CRAFT_STATUS_STYLE = {
    "natural_failure":  {"emoji": "💀", "label": "Échec catastrophique",  "color": discord.Color.dark_red()},
    "critical_failure": {"emoji": "❌", "label": "Échec critique",         "color": discord.Color.dark_gray()},
    "normal":           {"emoji": "🔨", "label": "Craft réussi",           "color": discord.Color.blurple()},
    "success":          {"emoji": "✅", "label": "Bonne réussite",         "color": discord.Color.green()},
    "critical_success": {"emoji": "⭐", "label": "Réussite critique",      "color": discord.Color.gold()},
    "natural_success":  {"emoji": "🌟", "label": "Réussite légendaire",    "color": discord.Color.teal()},
}

CRAFT_STATUS_DESCRIPTION = {
    "natural_failure": [
        "Un désastre complet. Les matériaux sont perdus et le résultat est inutilisable.",
        "Tout s'est effondré. Même les ingrédients n'ont pas survécu à la catastrophe.",
        "Une erreur fatale dès le début. Il vaut mieux ne pas en parler.",
        "Le pire scénario possible. Le travail est à refaire de zéro.",
        "Les dieux du craft regardaient ailleurs. Dommage.",
    ],
    "critical_failure": [
        "Quelque chose s'est mal passé. Le produit obtenu est de mauvaise qualité.",
        "Un faux mouvement au mauvais moment. Le résultat en pâtit sévèrement.",
        "La concentration a fait défaut au moment crucial.",
        "Le geste était imprécis, le résultat l'est tout autant.",
        "Une erreur de jugement qui coûte cher.",
    ],
    "normal": [
        "Un travail honnête. Le craft s'est déroulé sans accroc.",
        "Rien d'extraordinaire, mais le boulot est fait.",
        "Propre et fonctionnel. Pas de surprise dans un sens comme dans l'autre.",
        "Du travail solide, sans fioritures.",
        "Le résultat est conforme aux attentes. Ni plus, ni moins.",
    ],
    "success": [
        "Un beau travail. La maîtrise du craft se fait ressentir.",
        "Chaque étape s'est enchaînée avec fluidité.",
        "Le coup de main est là. Le résultat est au-dessus de la moyenne.",
        "Une belle exécution, menée avec assurance.",
        "Le craft a répondu comme espéré. Satisfaisant.",
    ],
    "critical_success": [
        "Exceptionnel. Chaque geste était parfait.",
        "Une maîtrise rare s'est exprimée aujourd'hui.",
        "Tout s'est aligné : la technique, la concentration, le moment.",
        "Un résultat qui dépasse les attentes de loin.",
        "Le genre de craft dont on se souvient longtemps.",
    ],
    "natural_success": [
        "Un chef-d'œuvre. Ce genre de réussite ne s'explique pas.",
        "Les astres étaient alignés. Un résultat hors du commun.",
        "Même les plus expérimentés ne réussiraient pas à expliquer comment.",
        "Une œuvre d'une perfection inexplicable.",
        "La chance et le talent réunis en un seul instant.",
    ],
}

# ------------------- DICE OUTCOMES -------------------

COLOR_BY_OUTCOME = {
    "natural_fail":      discord.Color.dark_red(),
    "critical_fail":     discord.Color.dark_gray(),
    "saved_fail":        discord.Color.light_gray(),
    "normal":            discord.Color.blurple(),
    "cancelled_success": discord.Color.teal(),
    "natural_success":   discord.Color.gold(),
    "critical_success":  discord.Color.green(),
}

OUTCOME_STATUS = {
    "critical_fail":    "Échec critique",
    "natural_fail":     "Échec naturel",
    "saved_fail":       "Échec sauvé",
    "normal":           "Résultat normal",
    "natural_success":  "Succès naturel",
    "cancelled_success": "Succès annulé",
    "critical_success": "Succès critique",
}

BASIC_DICE_OUTCOMES = {
    "natural_fail": {
        "color": discord.Color.dark_red(),
        "descriptions": ["Quel fiasco !", "Catastrophique...", "Un désastre total !"],
        "status": "Échec naturel",
    },
    "critical_fail": {
        "color": discord.Color.dark_gray(),
        "descriptions": ["Raté de peu...", "Les dés sont cruels.", "Pas de chance."],
        "status": "Échec critique",
    },
    "saved_fail": {
        "color": discord.Color.light_gray(),
        "descriptions": ["Sauvé de justesse !", "Belle récupération !", "Un miracle de dernière minute !"],
        "status": "Échec sauvé",
    },
    "normal": {
        "color": discord.Color.blurple(),
        "descriptions": ["Pas mal.", "Ça passe.", "Dans la moyenne."],
        "status": "Résultat normal",
    },
    "cancelled_success": {
        "color": discord.Color.teal(),
        "descriptions": ["Si proche...", "Le destin en a décidé autrement.", "La chance tourne."],
        "status": "Succès annulé",
    },
    "natural_success": {
        "color": discord.Color.green(),
        "descriptions": ["Parfait !", "Exactement ce qu'il fallait !", "Aucune marge d'erreur !"],
        "status": "Succès naturel",
    },
    "critical_success": {
        "color": discord.Color.gold(),
        "descriptions": ["Quelle dextérité !", "Magistral !", "Absolument parfait !"],
        "status": "Succès critique",
    },
}

STAT_DICE_OUTCOMES = {
    "attaque": {
        "natural_fail":       ["{character} se blesse en voulant attaquer.", "Un enchaînement catastrophique {de_character} — pire qu'un simple raté.", "L'arme {de_character} se retourne contre lui·elle."],
        "critical_fail":    ["L'arme glisse entre les doigts {de_character}...", "Un coup dans le vide, {character} aurait pu faire mieux les yeux fermés.", "Même un aveugle aurait mieux visé que {character}."],
        "normal":           ["Frappe correcte de la part {de_character}.", "{character} atteint sa cible.", "Un coup propre, sans éclat pour {character}."],
        "natural_success":    ["Une frappe puissante {de_character}, au-delà des attentes.", "{character} dépasse ses propres limites — le coup porte fort.", "Pas un critique, mais presque : {character} frappe avec autorité."],
        "critical_success": ["Coup dévastateur {de_character} !", "Une précision redoutable pour {character} !", "{character} fait mouche avec maestria !"],
    },
    "force": {
        "natural_fail":       ["{character} se froisse un muscle dans l'effort.", "Un effort contre-productif {de_character} — la situation empire.", "Les muscles {de_character} lâchent au pire moment."],
        "critical_fail":    ["Un effort pitoyable {de_character}.", "Même une plume aurait résisté à {character}.", "Les muscles {de_character} refusent de coopérer."],
        "normal":           ["Effort solide {de_character}.", "La puissance {de_character} est au rendez-vous.", "Un résultat dans la norme pour {character}."],
        "natural_success":    ["Une puissance remarquable {de_character}, au-delà de la moyenne.", "{character} repousse ses limites physiques.", "Les muscles {de_character} parlent d'eux-mêmes."],
        "critical_success": ["Force titanesque {de_character} !", "Un exploit de puissance pure pour {character} !", "Rien ne pouvait résister à {character} !"],
    },
    "défense": {
        "natural_fail":       ["{character} s'expose complètement en tentant de se protéger.", "La défense {de_character} crée une ouverture béante.", "En voulant bloquer, {character} aggrave sa position."],
        "critical_fail":    ["Aucune protection, le coup passe en entier sur {character}.", "Une défense en carton {de_character}.", "Même lever le bras aurait mieux fait pour {character}."],
        "normal":           ["Défense correcte {de_character}.", "{character} absorbe le coup.", "La protection {de_character} fait son travail."],
        "natural_success":    ["Une défense solide {de_character}, au-delà des attentes.", "{character} tient bon avec brio.", "La garde {de_character} est impressionnante."],
        "critical_success": ["La défense {de_character} est impénétrable !", "Rien ne passe la garde {de_character} !", "{character} est un rempart absolu !"],
    },
    "résistance": {
        "natural_fail":       ["{character} s'effondre bien avant d'avoir pu tenir.", "Le corps {de_character} capitule sans combat.", "Une résistance nulle — {character} cède immédiatement."],
        "critical_fail":    ["Le corps {de_character} lâche complètement.", "{character} s'effondre sous le poids de l'effort.", "La résistance {de_character} vole en éclats."],
        "saved_fail":       ["Ça fait mal, mais {character} tient.", "Le corps {de_character} flanche, l'esprit compense.", "Une résistance chancelante {de_character}, mais suffisante."],
        "normal":           ["{character} encaisse.", "Le corps {de_character} tient bon.", "Une endurance dans la moyenne pour {character}."],
        "natural_success":    ["{character} encaisse comme un roc.", "Une résistance au-dessus de la norme pour {character}.", "Le corps {de_character} répond présent, bien au-delà des attentes."],
        "critical_success": ["{character} est indestructible !", "Rien n'entame la résistance {de_character} !", "{character} est un roc face à l'adversité !"],
    },
    "agilité": {
        "natural_fail":       ["{character} trébuche et aggrave la situation.", "Un mouvement raté {de_character} qui empire les choses.", "La maladresse {de_character} atteint des sommets inédits."],
        "critical_fail":    ["Un faux pas magistral {de_character}.", "{character} a les deux pieds dans le même sabot.", "La grâce d'une pierre pour {character}."],
        "normal":           ["Un mouvement fluide {de_character}.", "L'agilité {de_character} est au rendez-vous.", "Ni trop vif, ni trop lent pour {character}."],
        "natural_success":    ["{character} se déplace avec une fluidité remarquable.", "Vif et précis, {character} dépasse les attentes.", "Un enchaînement de mouvements impressionnant {de_character}."],
        "critical_success": ["{character} est d'une vivacité époustouflante !", "{character} est insaisissable !", "Le vent lui-même ne suit pas {character} !"],
    },
    "discrétion": {
        "natural_fail":       ["{character} attire tous les regards au pire moment.", "Un fracas inattendu {de_character} — impossible de faire plus discret dans le mauvais sens.", "Même en se cachant, {character} se fait repérer."],
        "critical_fail":    ["{character} est aussi discret qu'un éléphant.", "Tout le monde se retourne sur {character}.", "Un bruit suspect à chaque pas {de_character}."],
        "normal":           ["{character} passe sans se faire remarquer.", "Mouvement silencieux {de_character}.", "{character} disparaît dans l'ombre, sans éclat."],
        "natural_success":    ["{character} se fond dans le décor avec aisance.", "À peine une ombre — {character} maîtrise l'art du silence.", "Personne ne perçoit la présence {de_character}."],
        "critical_success": ["{character} est parfaitement invisible !", "{character} est un fantôme parmi les vivants !", "Personne ne saura jamais que {character} est passé par là."],
    },
    "perception": {
        "natural_fail":       ["{character} interprète complètement mal ce qu'il·elle voit.", "Une lecture erronée {de_character} — pire que ne rien voir.", "Les sens {de_character} le·la trahissent activement."],
        "critical_fail":    ["{character} est aveugle et sourd à ce qui l'entoure.", "Rien n'est remarqué {de_character}, absolument rien.", "Les sens {de_character} sont en vacances."],
        "normal":           ["{character} analyse correctement son environnement.", "Rien n'échappe à l'œil exercé {de_character}.", "Une lecture correcte de la situation pour {character}."],
        "natural_success":    ["{character} capte des détails que d'autres manqueraient.", "Un sens aiguisé {de_character} — rien ne lui échappe.", "L'œil {de_character} est remarquablement précis."],
        "critical_success": ["Rien n'échappe au regard acéré {de_character} !", "{character} saisit chaque détail instantanément !", "Une perspicacité hors du commun pour {character} !"],
    },
    "infiltration": {
        "natural_fail":       ["{character} déclenche une alarme en essayant de se faufiler.", "L'infiltration {de_character} tourne à la catastrophe totale.", "Non seulement repéré·e, mais {character} compromet toute l'opération."],
        "critical_fail":    ["{character} est repéré avant même d'entrer.", "Une entrée en fanfare {de_character}, involontaire.", "L'infiltration {de_character} tourne au désastre."],
        "normal":           ["L'infiltration {de_character} se déroule sans accroc.", "{character} passe entre les mailles.", "{character} est discret et efficace."],
        "natural_success":    ["{character} navigue dans l'ombre avec une aisance remarquable.", "Une infiltration propre et maîtrisée {de_character}.", "Les gardes ne verront jamais {character} passer."],
        "critical_success": ["Une infiltration {de_character} digne des légendes !", "{character} est invisible, inaudible, introuvable !", "Personne ne saura jamais que {character} est passé par là."],
    },
    "charisme": {
        "natural_fail":       ["{character} offense involontairement son interlocuteur.", "Les mots {de_character} se retournent contre lui·elle.", "Une intervention catastrophique {de_character} — le silence aurait mieux valu."],
        "critical_fail":    ["{character} peine à articuler le moindre mot cohérent.", "Les mots {de_character} tombent dans un silence gêné.", "Même un mur aurait mieux répondu que {character}."],
        "normal":           ["{character} s'exprime avec aisance.", "Les mots {de_character} trouvent leur cible.", "Une présence correcte pour {character}."],
        "natural_success":    ["{character} capte l'attention de la salle.", "Les mots {de_character} portent bien au-delà des attentes.", "Une présence magnétique {de_character} — difficile de l'ignorer."],
        "critical_success": ["{character} envoûte son auditoire !", "Chaque mot {de_character} porte avec une grâce déconcertante !", "Impossible de résister au charme {de_character} !"],
    },
}


CHRONICLE_TITLES = [
    "📜 Les Chroniques des Dés",
    "📜 Le Grand Livre des Jets",
    "📜 Les Archives du Destin",
]

BEST_ROLLER_FLAVOR = [
    "Les dieux des dés semblent lui sourire... pour l'instant.",
    "La chance ou le talent ? Probablement la chance.",
    "Quelqu'un a triché ? On ne dit pas qui.",
]

WORST_ROLLER_FLAVOR = [
    "Les dés ne mentent pas. Eux, si.",
    "A besoin de nouveaux dés. Ou d'un exorcisme.",
    "Statistiquement remarquable... dans le mauvais sens.",
]

MOST_ROLLS_FLAVOR = [
    "Incapable de prendre une décision sans lancer un dé.",
    "A passé plus de temps à lancer qu'à réfléchir.",
    "Les dés sont son langage maternel.",
]
