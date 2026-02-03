import importlib
import os
import socket
import threading
from typing import Callable, Dict, List, Optional, Tuple

BUFFER_SIZE = 4096
HISTORY_LIMIT = 50


LANG_CHOICES = {
    "RU": {
        "lang_prompt": "Выберите язык интерфейса (RU/EN): ",
        "game_prompt": "Выберите игровой модуль по номеру: ",
        "game_list_header": "Доступные игровые модули:",
        "bind_success": "Сервер запущен и ожидает подключения.",
        "client_connected": "Пользователь подключился.",
        "client_disconnected": "Пользователь отключился.",
        "send_error": "Не удалось отправить сообщение клиенту.",
        "recv_error": "Произошла ошибка при получении сообщения.",
        "invalid_choice": "Некорректный выбор. Повторите попытку.",
    },
    "EN": {
        "lang_prompt": "Select interface language (RU/EN): ",
        "game_prompt": "Select game module by number: ",
        "game_list_header": "Available game modules:",
        "bind_success": "Server is running and awaiting connections.",
        "client_connected": "A user has connected.",
        "client_disconnected": "A user has disconnected.",
        "send_error": "Failed to send message to client.",
        "recv_error": "An error occurred while receiving a message.",
        "invalid_choice": "Invalid choice. Please try again.",
    },
}


class GameServer:
    def __init__(self, host: str, port: int, lang: str, game_logic) -> None:
        self.host = host
        self.port = port
        self.lang = lang
        self.game_logic = game_logic
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: List[socket.socket] = []
        self.clients_lock = threading.Lock()
        self.history: List[str] = []

    def start(self) -> None:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(LANG_CHOICES[self.lang]["bind_success"])
        while True:
            client_socket, client_address = self.server_socket.accept()
            with self.clients_lock:
                self.clients.append(client_socket)
            self._send_history(client_socket)
            print(LANG_CHOICES[self.lang]["client_connected"])
            thread = threading.Thread(
                target=self._handle_client,
                args=(client_socket, client_address),
                daemon=True,
            )
            thread.start()

    def broadcast(self, message: str) -> None:
        if not message:
            return
        self.history.append(message)
        if len(self.history) > HISTORY_LIMIT:
            self.history = self.history[-HISTORY_LIMIT:]
        with self.clients_lock:
            for client in list(self.clients):
                try:
                    client.sendall(f"{message}\n".encode("utf-8"))
                except OSError:
                    print(LANG_CHOICES[self.lang]["send_error"])
                    self._remove_client(client)

    def _send_history(self, client_socket: socket.socket) -> None:
        if not self.history:
            return
        try:
            history_payload = "\n".join(self.history) + "\n"
            client_socket.sendall(history_payload.encode("utf-8"))
        except OSError:
            print(LANG_CHOICES[self.lang]["send_error"])

    def _remove_client(self, client_socket: socket.socket) -> None:
        with self.clients_lock:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
        try:
            client_socket.close()
        except OSError:
            pass

    def _handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        try:
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                message = data.decode("utf-8").strip()
                if not message:
                    continue
                try:
                    self.game_logic.handle_message(client_address, message)
                except Exception:
                    # тут лучше не падать, иначе ты потеряешь всю сессию сервера
                    print(LANG_CHOICES[self.lang]["recv_error"])
        except OSError:
            print(LANG_CHOICES[self.lang]["recv_error"])
        finally:
            self._remove_client(client_socket)
            print(LANG_CHOICES[self.lang]["client_disconnected"])


def load_game_module(module_name: str):
    module = importlib.import_module(f"games.{module_name}")
    return module


def select_language() -> str:
    while True:
        choice = input(LANG_CHOICES["RU"]["lang_prompt"]).strip().upper()
        if choice in LANG_CHOICES:
            return choice
        print(LANG_CHOICES["RU"]["invalid_choice"])


def select_game_module(lang: str) -> str:
    games_dir = os.path.join(os.path.dirname(__file__), "games")
    modules = [
        filename[:-3]
        for filename in os.listdir(games_dir)
        if filename.endswith(".py") and filename != "__init__.py"
    ]
    while True:
        print(LANG_CHOICES[lang]["game_list_header"])
        for index, module in enumerate(modules, start=1):
            game_module = load_game_module(module)
            game_logic = game_module.GameLogic(lang=lang, broadcast=lambda _: None)
            print(f"{index}. {game_logic.get_info()}")
        choice = input(LANG_CHOICES[lang]["game_prompt"]).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(modules):
            return modules[int(choice) - 1]
        print(LANG_CHOICES[lang]["invalid_choice"])


def main() -> None:
    lang = select_language()
    module_name = select_game_module(lang)
    game_module = load_game_module(module_name)
    server = GameServer(host="0.0.0.0", port=5000, lang=lang, game_logic=None)
    game_logic = game_module.GameLogic(lang=lang, broadcast=server.broadcast)
    server.game_logic = game_logic
    server.start()


if __name__ == "__main__":
    main()
