ITEM_NOTIFICATION_VARIATIONS: dict[str, list[str]] = {
    "npc_purchase": [
        "Tu tends quelques pièces à **{npc}** et glisses {qty}**{item}** dans ton sac.",
        "Marché conclu. Tu repars {de_npc} avec {qty}**{item}** sous le bras.",
        "Le regard de **{npc}** s'éclaire à ta pièce — tu obtiens {qty}**{item}**.",
        "Après une brève négociation, **{npc}** te remet {qty}**{item}**.",
        "Tu paies **{npc}** de bonne grâce et empochtes {qty}**{item}** sans tarder.",
    ],
    "player_gift": [
        "**{sender}** te tend {qty}**{item}** d'un air généreux.",
        "La main ouverte, **{sender}** te glisse {qty}**{item}** sans un mot.",
        "**{sender}** t'offre {qty}**{item}** — une attention inattendue.",
        "Tu reçois {qty}**{item}** de la part {de_sender}.",
        "**{sender}** dépose {qty}**{item}** entre tes mains.",
    ],
    "lootbox_cadavre": [
        "En fouillant {le_lootbox}, tu mets la main sur {items_desc}.",
        "Les poches {de_lootbox} ne sont pas vides — tu y trouves {items_desc}.",
        "Tu retournes {le_lootbox} avec soin et découvres {items_desc}.",
        "La dépouille {de_lootbox} dissimulait {items_desc}.",
        "Après quelques instants de fouille, tu extrais {items_desc} {de_lootbox}.",
    ],
    "lootbox_caisse": [
        "Tu fouilles {le_lootbox} et déniche {items_desc} au fond.",
        "La main plongée dans {le_lootbox}, tu ressors {items_desc}.",
        "Sous les copeaux et la paille, {de_lootbox} cachait {items_desc}.",
        "Tu soulèves le couvercle et fouilles {le_lootbox} — {items_desc} apparaît.",
        "Au terme d'une fouille minutieuse {de_lootbox}, tu trouves {items_desc}.",
    ],
    "lootbox_coffre": [
        "Tu soulèves le couvercle {de_lootbox} — {items_desc} repose à l'intérieur.",
        "Le mécanisme cède, {de_lootbox} s'ouvre : {items_desc} t'attend.",
        "**{lootbox}** révèle son contenu — {items_desc} brille dans l'obscurité.",
        "Le couvercle s'abat avec un claquement sourd. Dans {de_lootbox}, tu trouves {items_desc}.",
        "Après quelques efforts, {de_lootbox} livre son secret : {items_desc}.",
    ],
    "admin_give": [
        "Par un heureux concours de circonstances, {qty}**{item}** vient à toi.",
        "Sans explication apparente, {qty}**{item}** apparaît entre tes mains.",
        "Le destin te sourit — {qty}**{item}** est désormais tien.",
        "La fortune te tend la main : {qty}**{item}** t'échoit.",
        "Comme porté par le vent du sort, {qty}**{item}** se retrouve en ta possession.",
    ],
}
