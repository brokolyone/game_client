import json
import socket
import threading
from typing import Dict, Tuple

BUFFER_SIZE = 4096

LANG_CHOICES = {
    "RU": {
        "lang_prompt": "Выберите язык интерфейса (RU/EN): ",
        "connecting": "Выполняется попытка подключения...",
        "connected": "Вы успешно подключены к серверу.",
        "connection_failed": "Не удалось подключиться. Введите адрес и порт вручную.",
        "enter_host": "Введите IP-адрес сервера: ",
        "enter_port": "Введите порт сервера: ",
        "input_prompt": "> ",
        "recv_error": "Произошла ошибка при получении сообщений.",
        "send_error": "Произошла ошибка при отправке сообщения.",
    },
    "EN": {
        "lang_prompt": "Select interface language (RU/EN): ",
        "connecting": "Attempting to connect...",
        "connected": "You have successfully connected to the server.",
        "connection_failed": "Connection failed. Please enter host and port manually.",
        "enter_host": "Enter server IP address: ",
        "enter_port": "Enter server port: ",
        "input_prompt": "> ",
        "recv_error": "An error occurred while receiving messages.",
        "send_error": "An error occurred while sending a message.",
    },
}


def select_language() -> str:
    while True:
        choice = input(LANG_CHOICES["RU"]["lang_prompt"]).strip().upper()
        if choice in LANG_CHOICES:
            return choice
        print(LANG_CHOICES["RU"]["lang_prompt"])


def load_settings() -> Dict[str, str]:
    try:
        with open("settings.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        # если конфиг битый, ты все равно попробуешь подключиться вручную
        return {"host": "127.0.0.1", "port": 5000}


def connect_with_retry(sock: socket.socket, lang: str) -> Tuple[str, int]:
    settings = load_settings()
    host = settings.get("host", "127.0.0.1")
    port = int(settings.get("port", 5000))
    print(LANG_CHOICES[lang]["connecting"])
    try:
        sock.connect((host, port))
        return host, port
    except OSError:
        print(LANG_CHOICES[lang]["connection_failed"])
    while True:
        host = input(LANG_CHOICES[lang]["enter_host"]).strip()
        port_input = input(LANG_CHOICES[lang]["enter_port"]).strip()
        if not port_input.isdigit():
            continue
        port = int(port_input)
        try:
            sock.connect((host, port))
            return host, port
        except OSError:
            print(LANG_CHOICES[lang]["connection_failed"])


def receive_messages(sock: socket.socket, lang: str) -> None:
    try:
        while True:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
            message = data.decode("utf-8").strip()
            if message:
                print(f"\n{message}")
                print(LANG_CHOICES[lang]["input_prompt"], end="", flush=True)
    except OSError:
        print(LANG_CHOICES[lang]["recv_error"])


def main() -> None:
    lang = select_language()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_with_retry(sock, lang)
    print(LANG_CHOICES[lang]["connected"])
    threading.Thread(target=receive_messages, args=(sock, lang), daemon=True).start()
    try:
        while True:
            message = input(LANG_CHOICES[lang]["input_prompt"])
            try:
                sock.sendall(message.encode("utf-8"))
            except OSError:
                print(LANG_CHOICES[lang]["send_error"])
                break
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        try:
            sock.close()
        except OSError:
            pass


if __name__ == "__main__":
    main()
