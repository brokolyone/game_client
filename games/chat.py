from typing import Callable, Dict, Tuple


class GameLogic:
    def __init__(self, lang: str, broadcast: Callable[[str], None]) -> None:
        self.lang = lang
        self.broadcast = broadcast
        self.nicknames: Dict[Tuple[str, int], str] = {}

    def get_info(self) -> str:
        if self.lang == "RU":
            return "Чат: простой обмен сообщениями между игроками"
        return "Chat: simple message exchange between players"

    def handle_message(self, address: Tuple[str, int], message: str) -> None:
        if address not in self.nicknames:
            self.nicknames[address] = message
            self._announce_join(message)
            return
        nickname = self.nicknames[address]
        self.broadcast(f"{nickname}: {message}")

    def _announce_join(self, nickname: str) -> None:
        if self.lang == "RU":
            self.broadcast(f"Пользователь {nickname} присоединился к чату.")
        else:
            self.broadcast(f"User {nickname} has joined the chat.")
