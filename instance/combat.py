class Combat:
    PLAYER_SLOTS = {
        1: [(-2, 5)],
        2: [(-2, 6), (-3, 6)],
        3: [(-2, 6), (-3, 6), (-2, 5)],
        4: [(-2, 6), (-3, 6), (-2, 5), (-3, 6)],
        5: [(-2, 6), (-3, 6), (-2, 5), (-3, 5), (-4, 6)],
        6: [(-2, 6), (-3, 6), (-2, 5), (-3, 5), (-4, 6), (-2, 4)],
        7: [(-2, 6), (-3, 6), (-2, 5), (-3, 5), (-4, 6), (-4, 5), (-1, 5)],
        8: [(-2, 6), (-3, 6), (-2, 5), (-3, 5), (-4, 6), (-4, 5), (-1, 5), (-2, 4)],
    }

    def __init__(self):
        self.dead_enemies: list[dict] = []                    # {position, is_boss, name}
        self.player_positions: dict[str, tuple[int, int]] = {}
        self.pending_xp: dict[str, int] = {}
        self.pending_kills: set[str] = set()
        self.boss_kills: dict[str, list[str]] = {}
        self.total_damage: dict[str, int] = {}                # dégâts totaux par joueur

    def is_active(self) -> bool:
        return bool(self.player_positions)

    def start(self, player_names: list[str]):
        """Initialise les positions joueurs au début du combat."""
        if self.is_active():
            return
        n = min(len(player_names), max(self.PLAYER_SLOTS))
        slots = self.PLAYER_SLOTS.get(n, self.PLAYER_SLOTS[max(self.PLAYER_SLOTS)])
        self.player_positions = {
            name: slots[i] if i < len(slots) else (-2, 5)
            for i, name in enumerate(player_names)
        }

    def register_kill(self, enemy):
        """Mémorise un ennemi mort et accumule ses récompenses."""
        self.dead_enemies.append({
            "position": enemy.position,
            "is_boss": enemy.boss,
            "name": enemy.name,
        })
        xp_rewards = enemy.xp_reward(enemy.damage_log)
        for char_name, xp in xp_rewards.items():
            self.pending_xp[char_name] = self.pending_xp.get(char_name, 0) + xp
        for char_name, dmg in enemy.damage_log.items():
            if dmg > 0:
                self.pending_kills.add(char_name)
                self.total_damage[char_name] = self.total_damage.get(char_name, 0) + dmg
        if enemy.boss:
            for char_name, dmg in enemy.damage_log.items():
                if dmg > 0:
                    self.boss_kills.setdefault(char_name, []).append(enemy.enemy_id)

    def collect_rewards(self) -> dict:
        """Retourne les récompenses accumulées et remet l'état à zéro."""
        rewards = {
            "xp": dict(self.pending_xp),
            "kills": set(self.pending_kills),
            "boss_kills": dict(self.boss_kills),
            "total_damage": dict(self.total_damage),
            "defeated_enemies": [{"name": d["name"], "is_boss": d["is_boss"]} for d in self.dead_enemies],
        }
        self.pending_xp.clear()
        self.pending_kills.clear()
        self.boss_kills.clear()
        self.total_damage.clear()
        self.dead_enemies.clear()
        self.player_positions.clear()
        return rewards
