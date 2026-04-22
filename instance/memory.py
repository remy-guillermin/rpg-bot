
from utils.path import GSHEET_MEMORIES
from utils.load import load_memories


class MemoryFragment:
    def __init__(self, player:str, id: int, name: str, content: str):
        self.player = player
        self.id = id
        self.name = name
        self.content = content
        self.unlocked = False
    

class Memory:
    def __init__(self):
        self.fragments = {}
        self.reload()
    
    def reload(self):
        self.fragments.clear()
        memories_data = load_memories(GSHEET_MEMORIES)
        for mem in memories_data:
            self.add_fragment(mem['player'], int(mem['id']), mem['name'], mem['content'])
        
    def add_fragment(self, player: str, id: int, name: str, content: str):
        self.fragments[f"{player}_{id}"] = MemoryFragment(player, id, name, content)
    
    def get_fragment(self, player: str, id: int) -> MemoryFragment:
        return self.fragments.get(f"{player}_{id}")

    def get_all_fragments_for_player(self, player: str):
        return [frag for key, frag in self.fragments.items() if frag.player == player]
    