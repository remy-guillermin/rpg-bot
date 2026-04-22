import discord
import json

from utils.db import get_connection


class Buff():
    """
    Variation temporaire des caractéristiques d'un personnage, généralement causée par l'utilisation d'un pouvoir ou la consommation d'un objet.
    """
    def __init__(
        self, 
        name: str, 
        description: str, 
        duration: int, 
        effects: dict,
        character_name: str,
        source: str
    ):
        self.name = name
        self.description = description
        self.duration = duration
        self.effects = effects
        self.character_name = character_name
        self.source = source


class BuffRepository():
    """
    Repository pour gérer les buffs.
    """
    def __init__(self, history):
        self.buffs = []
        self.history = history
        self.auto_decrement = True
        self.reload()

    def reload(self):
        self.buffs.clear()
        with get_connection() as conn:
            for row in conn.execute(
                "SELECT name, description, duration, effects, character_name, source FROM buffs"
            ):
                self.buffs.append(Buff(
                    name=row["name"],
                    description=row["description"],
                    duration=row["duration"],
                    effects=json.loads(row["effects"]),
                    character_name=row["character_name"],
                    source=row["source"],
                ))
    
    def toggle_auto_decrement(self):
        self.auto_decrement = not self.auto_decrement

    def set_auto_decrement(self, active: bool):
        self.auto_decrement = active


    async def add_buff(self, guild: discord.Guild, buff: Buff):
        self.buffs.append(buff)
        self.save()
        await self.history.log_buff_application(guild, buff.character_name, buff.name, buff.source, buff.duration, buff.effects, self.auto_decrement)

    def get_buff_by_name_and_character(self, name: str, character_name: str) -> Buff | None:
        for buff in self.buffs:
            if buff.name == name and buff.character_name == character_name:
                return buff
        return None

    def remove_buff_by_name_and_character(self, name: str, character_name: str):
        buff = self.get_buff_by_name_and_character(name, character_name)
        if buff:
            self.buffs.remove(buff)
            self.save()

    def update_buff(self, name: str, character_name: str, **kwargs):
        buff = self.get_buff_by_name_and_character(name, character_name)
        if not buff:
            raise ValueError(f"Buff '{name}' not found.")
        for key, value in kwargs.items():
            if hasattr(buff, key):
                setattr(buff, key, value)
        self.save()
    
    def list_buffs(self) -> list[Buff]:
        return self.buffs   
    
    def clear_buffs(self):
        self.buffs = []
        self.save()

    def clear_buffs_by_character(self, character_name: str):
        self.buffs = [buff for buff in self.buffs if buff.character_name != character_name]
        self.save()

    def get_buffs_by_character(self, character_name: str):
        return [buff for buff in self.buffs if buff.character_name == character_name]

    async def decrement_buffs_duration(self, guild: discord.Guild, character_name: str, force: bool = False):
        if self.auto_decrement or force:
            expired = []
            for buff in self.get_buffs_by_character(character_name):
                buff.duration -= 1
                if buff.duration <= 0:
                    expired.append(buff)
            for buff in expired:
                self.buffs.remove(buff)
                await self.history.log_buff_expiration(guild, buff.character_name, buff.name, buff.source, buff.effects)
            self.save()

    def increment_buffs_duration(self, character_name: str):
        for buff in self.get_buffs_by_character(character_name):
            buff.duration += 1
        self.save()




    def save(self):
        with get_connection() as conn:
            conn.execute("DELETE FROM buffs")
            conn.executemany(
                "INSERT INTO buffs (character_name, name, description, duration, effects, source) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (b.character_name, b.name, b.description, b.duration, json.dumps(b.effects), b.source)
                    for b in self.buffs
                ],
            )