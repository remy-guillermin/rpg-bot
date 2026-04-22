import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import io

from utils.utils import (
    BG_COLOR,
    TEAL,
    TEAL_DIM,
    STATS_CLEAN,
    _get_stat_bonus,
    _get_resource_max_bonus,
    _get_active_sets,
    SET_RESOURCE_MAX_MAP,
)

from instance.character import Character

def _build_status_block(character: Character) -> str:
    """
        Génère une image représentant les ressources du personnage (HP, Mana, Stamina) sous forme de barres de statut.

    Parameters
    ----------
    character : Character
        Le personnage pour lequel générer les barres de statut.

    Returns
    -------
    str
        Le chemin vers le fichier image généré.
    """
    hp_base, hp_level, hp_item       = _get_resource_max_bonus("hp", character)
    mana_base, mana_level, mana_item  = _get_resource_max_bonus("mana", character)
    stam_base, stam_level, stam_item  = _get_resource_max_bonus("stamina", character)

    hp_current      = character.resources.get("hp", 0)
    mana_current    = character.resources.get("mana", 0)
    stam_current = character.resources.get("stamina", 0)

    stats = {
        "HP":      (hp_current,      hp_base,      hp_level,      hp_item,      "#e63946", "#ff6b6b", "#ff9999"),
        "Mana":    (mana_current,    mana_base,    mana_level,    mana_item,    "#99ccee", "#6aafd6", "#457b9d"),
        "Stamina": (stam_current,    stam_base,    stam_level,    stam_item,    "#2d6a4f", "#52b788", "#95d5b2"),
    }

    fig, ax = plt.subplots(figsize=(6, 2.5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    bar_height = 0.4
    bar_max_width = 1.0
    y_positions = [2, 1, 0]
    radius = 0.1

    def draw_pill(ax, x, y, width, height, color, radius, alpha=1.0, zorder=3, linewidth=1, linestyle='-'):
        if width <= 0:
            return
        r = min(radius, width / 2, height / 2)
        box = FancyBboxPatch(
            (x, y - height / 2),
            width, height,
            boxstyle=f"round,pad=0,rounding_size={r}",
            linewidth=linewidth,
            linestyle=linestyle,
            facecolor=color,
            alpha=alpha,
            zorder=zorder,
            clip_on=True,
        )
        ax.add_patch(box)


    for (label, (current, base, level_bonus, item_bonus, color_base, color_level, color_item)), y in zip(stats.items(), y_positions):
        total_max = base + level_bonus + item_bonus
        if total_max == 0:
            continue

        ratio_current  = current / total_max
        ratio_base     = base / total_max
        ratio_level    = (base + level_bonus) / total_max
        ratio_item     = 1.0

        # Fond
        draw_pill(ax, 0, y, bar_max_width, bar_height, "#2e2e4e", radius)

        # Valeur actuelle (overlay semi-transparent)
        draw_pill(ax, 0, y, ratio_current * bar_max_width, bar_height, color_base, radius)

        if (item_bonus > 0 or level_bonus > 0) and (current == total_max):
            draw_pill(ax, 0, y, ratio_base * bar_max_width, bar_height, "none", radius, linestyle='--', zorder=4)
    
        
        if level_bonus > 0 and item_bonus > 0 and current == total_max:
            draw_pill(ax, 0, y, ratio_level * bar_max_width, bar_height, "none", radius, linestyle=':', zorder=5)
        
        draw_pill(ax, 0, y, bar_max_width, bar_height, "none", radius, zorder=6, linewidth=1.5)

        # Labels
        ax.text(-0.02, y, label, va="center", ha="right",
                color="white", fontsize=10, fontweight="bold")
        val_text = f"{current} / {total_max}"
        if level_bonus + item_bonus > 0:
            val_text += f"  (+{level_bonus + item_bonus})"
        ax.text(bar_max_width + 0.02, y, val_text, va="center", ha="left",
                color="#cccccc", fontsize=9)

    ax.set_xlim(-0.18, 1.45)
    ax.set_ylim(-0.6, 2.6)
    ax.axis("off")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _sort_radar(stats_dict):
    """Max haut-droite, min bas-gauche, décroissance symétrique."""
    sorted_items = sorted(
        stats_dict.items(), key=lambda x: x[1], reverse=True
    )
    N = len(sorted_items)
    positions = [None] * N
    left, right = 0, N - 1
    for i, item in enumerate(sorted_items):
        if i % 2 == 0:
            positions[left]  = item; left  += 1
        else:
            positions[right] = item; right -= 1
    return [x[0] for x in positions], [x[1] for x in positions]


def _build_stats_block(character: Character) -> str:
    """
        Génère une image représentant les statistiques du personnage (Force, Dextérité, Intelligence, etc.) sous forme de radar.

    Parameters
    ----------
    character : Character
        Le personnage pour lequel générer les barres de statistiques.
    
    Returns
    -------
    str
        Le chemin vers le fichier image généré.
    """  
    level_bonus = {}

    for lvl in range(1, character.level + 1):
        if lvl in character.level_upgrades:
            for stat_change in character.level_upgrades[lvl]:
                if stat_change[0] in level_bonus:
                    level_bonus[stat_change[0]] += stat_change[1]
                else:
                    level_bonus[stat_change[0]] = stat_change[1]

    item_bonus = {}
    equipped_entries = character.inventory.get_equipped_items()
    for entry in equipped_entries:
        item, qty = entry.item, entry.equipped_quantity
        for stat, bonus in item.equipped_bonus.items():
            clean = STATS_CLEAN.get(stat, stat)
            item_bonus[clean] = item_bonus.get(clean, 0) + bonus * qty
        for rune in entry.runes:
            for stat, bonus in rune.equipped_bonus.items():
                clean = STATS_CLEAN.get(stat, stat)
                item_bonus[clean] = item_bonus.get(clean, 0) + bonus

    for set_info in _get_active_sets(character):
        for stat, bonus in set_info["bonuses"].items():
            if stat not in SET_RESOURCE_MAX_MAP:
                item_bonus[stat] = item_bonus.get(stat, 0) + bonus

    final_stats = {
        k: v + item_bonus.get(k, 0) + level_bonus.get(k, 0)
        for k, v in character.stat_points.items()
    }

    level_stats = {
        k: v + level_bonus.get(k, 0)
        for k, v in character.stat_points.items()
    }

    has_item_bonus = bool(item_bonus)
    has_level_bonus = bool(level_bonus)

    # Ordre des axes déterminé par les stats BASE + LEVEL
    labels, with_level_vals = _sort_radar(level_stats)
    final_vals = [final_stats[k] for k in labels]
    base_vals = [character.stat_points[k] for k in labels]

    # Plage dynamique : toujours au moins BASE_MIN/BASE_MAX
    v_min = min(-3, min(final_vals))
    v_max = max(4, max(final_vals)+2)
    v_range = v_max - v_min

    def norm(v): return (v - v_min) / v_range
    
    N        = len(labels)
    angles   = np.linspace(0, 2 * np.pi, N, endpoint=False)
    r_final  = [norm(v) for v in final_vals]
    r_base   = [norm(v) for v in base_vals]
    r_lvl    = [norm(v) for v in with_level_vals]
    ac       = np.append(angles, angles[0])
    rf_c     = r_final + [r_final[0]]
    rb_c     = r_base  + [r_base[0]]
    rl_c     = r_lvl   + [r_lvl[0]]
    
    # ── Figure ────────────────────────────────────────
    fig, ax = plt.subplots(
        figsize=(6, 6), subplot_kw={'projection': 'polar'},
        dpi=150
    )
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_theta_zero_location('NE')
    ax.set_theta_direction(-1)

    label = ""

    # Anneaux

    step = 1 if v_max - v_min <= 10 else 2
    if v_min % 2 != 0:
        v_min -= 1

    if v_max % 2 != 0:
        v_max += 1

    for v in range(v_min, v_max, step):
        r     = norm(v)
        lw    = 1.8 if v == 0 else 0.7
        alpha = 0.55 if v == 0 else 0.3
        ring_a = np.linspace(0, 2 * np.pi, 200)
        ax.plot(ring_a, [r] * 200,
                color='#ffffff', lw=lw, alpha=alpha, zorder=1)

    # Forme de base (pointillés) — seulement si items équipés
    if has_item_bonus and has_level_bonus:
        label = "Avec équipements"
        
        ax.plot(ac, rb_c,
                color=TEAL_DIM, lw=1.5, ls='--',
                alpha=0.5, zorder=2, label='Base')
        ax.fill(ac, rb_c,
                color=TEAL_DIM, alpha=0.05, zorder=2)
                
        ax.plot(ac, rl_c,
                color=TEAL_DIM, lw=1.5, ls=':',
                alpha=0.5, zorder=2, label='Niveau')
        ax.fill(ac, rl_c,
                color=TEAL_DIM, alpha=0.05, zorder=2)
    
    elif has_level_bonus and not has_item_bonus:
        label = "Niveau"

        ax.plot(ac, rb_c,
                color=TEAL_DIM, lw=1.5, ls='--',
                alpha=0.5, zorder=2, label='Base')
        ax.fill(ac, rl_c,
                color=TEAL_DIM, alpha=0.05, zorder=2)
    elif has_item_bonus and not has_level_bonus:
        label = "Avec équipements"

        ax.plot(ac, rb_c,
                color=TEAL_DIM, lw=1.5, ls='--',
                alpha=0.5, zorder=2, label='Base')
        ax.fill(ac, rb_c,
                color=TEAL_DIM, alpha=0.05, zorder=2)

    # Forme finale (plein)
    ax.plot(ac, rf_c,
            color=TEAL, lw=2, zorder=3,
            label=label)
    ax.fill(ac, rf_c,
            color=TEAL, alpha=0.15, zorder=2)
    ax.scatter(angles, r_final,
               color=TEAL, s=40, zorder=4)

    # Labels des axes avec valeur finale
    tick_labels = []
    for i, lbl in enumerate(labels):
        v   = final_vals[i]
        bv  = base_vals[i]
        bon = item_bonus.get(lbl, 0)
        sign = '+' if v > 0 else ''
        if bon:
            tick_labels.append(f"{lbl}\n{sign}{v} [{bon:>+d}]")
        else:
            tick_labels.append(f"{lbl}\n{sign}{v}")

    ax.set_thetagrids(
        np.degrees(angles), tick_labels,
        fontsize=12, color='#aaaaaa'
    )
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.yaxis.grid(False)
    ax.xaxis.grid(False)
    # ax.xaxis.grid(True, color='#ffffff', alpha=0.08, lw=0.8)
    ax.spines['polar'].set_visible(False)

    

    if has_item_bonus or has_level_bonus:
        angle = np.deg2rad(67.5)

        ax.legend(loc='lower left', fontsize=8,
                  labelcolor='#aaaaaa',
                  facecolor='#202020', edgecolor='#202020',
                  bbox_to_anchor=(.5 + np.cos(angle)/2, .5 + np.sin(angle)/2))
    

    # Export en mémoire → BytesIO
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png',
                bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf            


def _build_hp_tracker(enemies: list) -> io.BytesIO:
    quantity = len(enemies)
    color = "#e63946"
    fig, ax = plt.subplots(figsize=(6, 0.8 * quantity))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    bar_height = 0.35
    bar_max_width = 1.0
    radius = 0.08
    y_positions = [2 - i * 0.8 for i in range(quantity)]

    def draw_pill(ax, x, y, width, height, color, radius):
        if width <= 0:
            return
        r = min(radius, width / 2, height / 2)
        box = FancyBboxPatch(
            (x, y - height / 2),
            width, height,
            boxstyle=f"round,pad=0,rounding_size={r}",
            linewidth=1,
            facecolor=color,
            zorder=3,
            clip_on=True,
        )
        ax.add_patch(box)

    for enemy, y in zip(enemies, y_positions):
        id = enemy.instance_id.split('_')[-1]
        ratio = (enemy.current_hp / enemy.max_hp) if enemy.max_hp else 0
        draw_pill(ax, 0, y, bar_max_width, bar_height, "#2e2e4e", radius)
        draw_pill(ax, 0, y, ratio * bar_max_width, bar_height, color, radius)
        ax.text(-0.02, y, f"{enemy.name} {f'[{id}]' if not enemy.boss else ''}", va="center", ha="right",
                color="white", fontsize=10, fontweight="bold")
        val_text = f"{enemy.current_hp} / {enemy.max_hp}"
        ax.text(bar_max_width + 0.02, y, val_text, va="center", ha="left",
                color="#cccccc", fontsize=9)

    ax.set_xlim(-0.18, 1.45)
    ax.set_ylim(min(y_positions) - 0.6, max(y_positions) + 0.6)
    ax.axis("off")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf