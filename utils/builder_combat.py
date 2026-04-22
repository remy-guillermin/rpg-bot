from PIL import Image, ImageDraw, ImageColor, ImageFilter, ImageFont
import os
import math
import random
import numpy as np
from itertools import groupby

from utils.utils import PLAYER_COLORS, PLAYER_INITIALS

BOSS_COLOR   = '#6A1B9A'
ENEMY_COLOR  = '#C62828'
PLAYER_COLOR = '#1565C0'

def _is_light_color(hex_color: str) -> bool:
    r, g, b = ImageColor.getrgb(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance > 0.5

W, H = 2400, 1800

def midpoint_displace(pts, roughness=0.55, iterations=5):
    """
    Déplacement de point médian fractal sur un polygone fermé.
    roughness : 0 = lisse, 1 = très chaotique
    iterations : nombre de subdivisions (double le nb de points à chaque fois)
    """
    current = list(pts)
    scale = 1.0

    for _ in range(iterations):
        next_pts = []
        n = len(current)
        for i in range(n):
            p1 = current[i]
            p2 = current[(i + 1) % n]

            # Point médian
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2

            # Normale à l'arête
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = math.hypot(dx, dy)
            nx, ny = (-dy / length, dx / length) if length > 0 else (0, 1)

            # Décalage aléatoire le long de la normale
            offset = (random.random() - 0.5) * 2 * scale * length * roughness

            next_pts.append(p1)
            next_pts.append((mx + nx * offset, my + ny * offset))

        current = next_pts
        scale *= 0.5   # amplitude divisée par 2 à chaque itération

    return current

def expand_polygon(pts, cx, cy, margin):
    expanded = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        dist = math.hypot(dx, dy)
        if dist > 0:
            expanded.append((x + dx / dist * margin,
                             y + dy / dist * margin))
    return expanded

def draw_line_triangle(draw, cx, cy, size=80, angle_deg=0, n_lines=5, color='#1A1208', width=5):
    """
    angle_deg : direction de la pointe (0 = haut, 90 = droite, 180 = bas, 270 = gauche)
    """
    rad = math.radians(angle_deg)

    # Vecteur de la pointe vers la base
    tip_dx =  math.sin(rad)
    tip_dy = -math.cos(rad)

    # Vecteur perpendiculaire (direction des lignes)
    perp_dx =  math.cos(rad)
    perp_dy =  math.sin(rad)

    for i in range(n_lines):
        t = i / (n_lines - 1)   # 0 = pointe, 1 = base

        half_w = t * size / 2
        along  = (t - 0.5) * size   # déplacement le long de l'axe

        # Centre de la ligne courante
        lx = cx + along * tip_dx
        ly = cy + along * tip_dy

        # Endpoints
        x1 = lx - half_w * perp_dx
        y1 = ly - half_w * perp_dy
        x2 = lx + half_w * perp_dx
        y2 = ly + half_w * perp_dy

        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

def on_floor(x, y, floor_arr):
    xi, yi = int(x), int(y)
    if 0 <= xi < W and 0 <= yi < H:
        return floor_arr[yi, xi] > 128
    return False

def dotted_line(draw, p1, p2, color, floor_arr, dot_radius=2, spacing=12):
    x1, y1 = p1
    x2, y2 = p2
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    steps = int(length / spacing)
    for i in range(steps + 1):
        t = i / max(steps, 1)
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        if on_floor(x, y, floor_arr):
            draw.ellipse([(x - dot_radius, y - dot_radius),
                          (x + dot_radius, y + dot_radius)], fill=color)

def draw_hex_grid(draw, cx, cy, floor_arr, hex_size=40, color='#9A8C7A'):
    col_w = math.sqrt(3) * hex_size
    row_h = 1.5 * hex_size
    n_cols = int(W / col_w) + 4
    n_rows = int(H / row_h) + 4

    # Offset pour que l'origine de la grille tombe sur (cx, cy)
    offset_x = cx % col_w
    offset_y = cy % row_h

    hex_centers = []
    for row in range(-2, n_rows + 2):
        for col in range(-2, n_cols + 2):
            x = col * col_w + (row % 2) * (col_w / 2) + offset_x
            y = row * row_h + offset_y

            hex_centers.append((x, y))

            pts = [
                (x + hex_size * math.cos(math.radians(60 * k - 30)),
                 y + hex_size * math.sin(math.radians(60 * k - 30)))
                for k in range(6)
            ]

            for k in range(6):
                p1 = pts[k]
                p2 = pts[(k + 1) % 6]
                if on_floor(*p1, floor_arr) and on_floor(*p2, floor_arr):
                    dotted_line(draw, p1, p2, color=color, floor_arr=floor_arr, dot_radius=2, spacing=14)

    return hex_centers

def pixel_to_hex(px, py, hex_size, cx, cy):
    """Pixel → coordonnées axiales (q, r) — pointy-top"""
    # Position relative au centre
    x = px - cx
    y = py - cy

    q = (x * math.sqrt(3)/3 - y / 3) / hex_size
    r = (y * 2/3) / hex_size

    return hex_round(q, r)

def hex_round(q, r):
    """Arrondit des coordonnées hex fractionnaires à l'hex le plus proche"""
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)

    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs

    return (rq, rr)

def hex_to_pixel(q, r, hex_size, cx, cy):
    """Coordonnées axiales (q, r) → pixel — pointy-top"""
    x = hex_size * (math.sqrt(3) * q + math.sqrt(3)/2 * r) - hex_size * math.sqrt(3) / 2
    y = hex_size * (3/2 * r)

    return (cx + x, cy + y)

def draw_glow(overlay, x, y, radius, color_hex, intensity=120, blur_radius=20):
    """Dessine un glow flou autour d'un point."""
    glow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    glow_draw  = ImageDraw.Draw(glow_layer)

    r, g, b = ImageColor.getrgb(color_hex)

    # Plusieurs cercles concentriques du plus grand au plus petit
    for i in range(6, 0, -1):
        alpha = int(intensity * (i / 6) ** 2)
        r_i   = radius + blur_radius * i // 2
        glow_draw.ellipse(
            [(x - r_i, y - r_i), (x + r_i, y + r_i)],
            fill=(r, g, b, alpha)
        )

    # Flou gaussien pour adoucir
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    overlay.alpha_composite(glow_layer)

def draw_enemy(draw, overlay, x, y, hp_current, hp_max, enemy_name="", is_boss=False, label="?"):
    color = BOSS_COLOR if is_boss else ENEMY_COLOR
    radius = 35 if is_boss else 15

    if is_boss:
        draw_glow(overlay, x, y, radius, color, intensity=140, blur_radius=25)

    # Cercle de base
    draw.circle((x, y), radius, fill=color)
    font = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', size=24)

    if not is_boss:
        draw.text((x, y), label, fill='white', anchor='mm', font=font)

    # Barre de vie
    hp_ratio = hp_current / hp_max if hp_max > 0 else 0
    bar_width = radius * 2
    bar_height = 4
    bar_x1 = x - radius
    bar_y1 = y + radius + 5
    bar_x2 = bar_x1 + bar_width * hp_ratio
    bar_y2 = bar_y1 + bar_height
    bar_x3 = bar_x1 + bar_width
    bar_y3 = bar_y1 + bar_height

    draw.rectangle([(bar_x1, bar_y1), (bar_x3, bar_y3)], fill='gray', outline='black', width=1)
    draw.rectangle([(bar_x1, bar_y1), (bar_x2, bar_y2)], fill='red', outline='black', width=1)

def draw_dead_enemy(draw, x, y, is_boss=False):
    radius = 35 if is_boss else 12
    draw.circle((x, y), radius, fill='#606060', outline='#303030', width=2)


def draw_player(draw, x, y, player_name, outline='#000000'):
    radius = 25
    color = PLAYER_COLORS.get(player_name, PLAYER_COLOR)
    draw.circle((x, y), radius, fill=color, outline=outline, width=3)
    initials = PLAYER_INITIALS.get(player_name, player_name[:2].upper())
    font = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', size=16)
    text_color = '#000000' if _is_light_color(color) else '#FFFFFF'
    draw.text((x, y), initials, fill=text_color, anchor='mm', font=font)


# Mapping : q → lettre, r → chiffre
def hex_to_chess(q, r):
    # Décaler pour commencer à A/1 (q_min = -11, r_min = -11)
    col = q + 11          # 0 → 21
    row = r + 11          # 0 → 21
    letter = chr(ord('A') + col)
    return f"{letter}{row + 1}"

def chess_to_hex(notation: str) -> tuple[int, int]:
    """Convertit une notation échecs (ex: 'L12') en coordonnées axiales (q, r)."""
    notation = notation.strip().upper()
    col = ord(notation[0]) - ord('A')
    row = int(notation[1:]) - 1
    return (col - 11, row - 11)

def draw_combat(enemies, players, dead_enemies=None, room_type='cavern'):
    BG_COLOR     = '#CCBBA3' if room_type == 'cavern' else '#1E3231'
    FLOOR_COLOR  = '#EBE3D3' if room_type == 'cavern' else '#9CB285'
    OUTLINE      = '#000000' if room_type == 'cavern' else '#010206'

    img  = Image.new('RGBA', (W, H), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # random.seed(42)

    # ─── Forme de base (peu de points = formes variées et asymétriques) ───────────
    cx, cy = W // 2, H // 2
    base_r = 700
    n_base = 35

    angles_base = [i * 2 * math.pi / n_base for i in range(n_base)]

    # Légère variation du rayon de base pour éviter un cercle parfait
    base_pts = [
        (cx + (base_r + random.randint(-80, 80)) * math.cos(a),
        cy + (base_r + random.randint(-80, 80)) * math.sin(a))
        for a in angles_base
    ]

    floor_pts = midpoint_displace(base_pts, roughness=0.55, iterations=10)

    shadow_pts = [(x - 20, y - 10) for x, y in floor_pts]

    triangle_pts = expand_polygon(floor_pts[::150], cx, cy, margin=30)

    # ─── Dessin ───────────────────────────────────────────────────────────────────
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.polygon(floor_pts, fill=(0, 0, 0, 120))  # polygone étendu
    overlay_draw.polygon(shadow_pts,  fill=(0, 0, 0, 0)) 


    for x, y in triangle_pts:
        draw_line_triangle(draw, x, y, size=80, angle_deg=np.random.randint(0, 360), n_lines=6, color=OUTLINE, width=5)

    # ─── Masque du sol ────────────────────────────────────────────────────────────
    floor_mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(floor_mask).polygon(floor_pts, fill=255)
    floor_arr = np.array(floor_mask)

        
    draw.polygon(floor_pts, fill=FLOOR_COLOR)

    hex_centers = draw_hex_grid(draw, cx, cy, floor_arr, hex_size=45, color='#8A7A68')

    # ─── Labels de coordonnées sur les cases libres ───────────────────────────────
    occupied_positions = set()
    for e in enemies.values():
        occupied_positions.add(e['position'])
    for pos in players.values():
        occupied_positions.add(pos)
    if dead_enemies:
        for dead in dead_enemies:
            occupied_positions.add(dead['position'])

    label_font = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', size=14)
    label_color = '#7A6A58' if room_type == 'cavern' else '#3A5030'
    for q in range(-10, 11):
        for r in range(-10, 11):
            if (q, r) in occupied_positions:
                continue
            lx, ly = hex_to_pixel(q, r, hex_size=45, cx=cx, cy=cy)
            if on_floor(lx, ly, floor_arr):
                draw.text((lx, ly), hex_to_chess(q, r), fill=label_color, anchor='mm', font=label_font)

    for enemy_name, enemy in enemies.items():
        ex, ey = hex_to_pixel(*enemy['position'], hex_size=45, cx=cx, cy=cy)
        draw_enemy(draw, overlay, ex, ey, enemy['hp_current'], enemy['hp_max'], enemy_name=enemy_name, is_boss=enemy['boss'], label=enemy.get('label', '?'))

    for player_name, (px, py) in players.items():
        px, py = hex_to_pixel(px, py, hex_size=45, cx=cx, cy=cy)
        draw_player(draw, px, py, player_name, outline=OUTLINE)

    if dead_enemies:
        for dead in dead_enemies:
            dx, dy = hex_to_pixel(*dead['position'], hex_size=45, cx=cx, cy=cy)
            draw_dead_enemy(draw, dx, dy, is_boss=dead.get('is_boss', False))

    for i in range(len(floor_pts)):
        draw.line([floor_pts[i], floor_pts[(i + 1) % len(floor_pts)]],
                fill=OUTLINE, width=7)

    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    # ─── Sauvegarde ───────────────────────────────────────────────────────────────
    out = 'combat.png'
    folder = 'data/combat_images/'
    if not os.path.exists(folder):
        os.makedirs(folder)
    img.save(os.path.join(folder, out))
    return out