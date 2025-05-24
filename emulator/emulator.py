import asyncio
import websockets
import requests
import random
import json
import time
from datetime import datetime

SERVER_URL = "http://localhost:8000" # конфигурация
WS_URL = "ws://localhost:8000/ws"
TEAM_NAME = "bot_team"
HEADERS = {}
TOKEN = None

def register(): #получение токена
    global TOKEN, HEADERS
    response = requests.post(f"{SERVER_URL}/teams/login", params={"name": TEAM_NAME})
    if response.status_code == 200:
        TOKEN = response.json()["token"]
        HEADERS = {"Authorization": f"Bearer {TOKEN}"}
        print(f"[INFO] Зарегистрирован как '{TEAM_NAME}'")
    else:
        print("[ERROR] Не удалось зарегистрироваться:", response.text)
        exit()


def get_task(): # получить задачу
    response = requests.get(f"{SERVER_URL}/task", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None

def send_solution(task): # отправление решения
    task_id = task["taskId"]
    answer = {
        "selections": [
            {
                "type": "ЛОГИЧЕСКАЯ ОШИБКА",
                "startSelection": random.randint(1, 100),
                "endSelection": random.randint(101, 300)
            }
        ]
    }
    payload = {
        "taskId": task_id,
        "answer": json.dumps(answer)
    }
    response = requests.post(f"{SERVER_URL}/solution", headers=HEADERS, json=payload)
    if response.status_code == 200:
        print(f"[✓] Отправлено решение для задачи {task_id}")
    else:
        print(f"[!] Ошибка при отправке решения: {response.text}")

async def emulate(): # имитация работы
    uri = f"{WS_URL}/{TEAM_NAME}"
    async with websockets.connect(uri) as websocket:
        print(f"[CONNECT] Установлено соединение по WebSocket как '{TEAM_NAME}'")
        while True:
            try:
                task = get_task()
                if task:
                    print(f"[TASK] Получена задача {task['taskId']}, ждем...")
                    await asyncio.sleep(random.randint(1, 5))
                    send_solution(task)
                else:
                    print("[WAIT] Нет доступных задач...")
                await asyncio.sleep(5)
            except Exception as e:
                print("[ERROR] Ошибка во время работы:", e)
                await asyncio.sleep(5)

if __name__ == "__main__":
    register()
    asyncio.run(emulate())
