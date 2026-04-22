from utils.db import load_location, save_location


class Location:
    """Tracks the current realm and optional city. Persisted across restarts via SQLite."""

    def __init__(self):
        self.realm: str
        self.city: str | None
        self.realm, self.city = load_location()

    def get_location(self) -> tuple[str, str | None]:
        return self.realm, self.city

    def set_realm(self, realm: str) -> None:
        self.realm = realm
        self.city = None
        save_location(self.realm, self.city)

    def set_city(self, city: str) -> None:
        self.city = city
        save_location(self.realm, self.city)

    def clear_city(self) -> None:
        self.city = None
        save_location(self.realm, self.city)
