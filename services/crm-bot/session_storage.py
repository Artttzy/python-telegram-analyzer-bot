from pyrogram import Client
import json
from requests import request
from requests.models import Response
from settings import session_dir
import settings
import base64
import os.path

url = 'http://146.0.78.143:5355'
# url = 'http://localhost:5254'


async def save_session(tg_id, session, api_id, api_hash, phone, sdk, app_version, device, language):

    payload = json.dumps({
        "telegramId": tg_id,
        "sessionString": session,
        "appId": api_id,
        "apiHash": api_hash,
        "phone": phone,
        "sdk": sdk,
        "appVersion": app_version,
        "device": device,
        "language": language
    })

    headers = {
        'ApiKey': settings.bridge_api_key,
        'Content-Type': 'application/json'
    }

    request(
        "POST", f'{url}/api/v1/users/add', headers=headers, data=payload)


async def load_sessions() -> list[Client]:
    payload = {}
    headers = {
        'ApiKey': settings.bridge_api_key
    }

    response: Response = request(
        "GET", f"{url}/api/v1/users", headers=headers, data=payload)

    json_body = response.json()

    items = []

    for item in json_body:

        telegram_id = item["telegramId"]
        session_string = item["sessionString"]
        # session_string = session_string[0]

        filename = f"{session_dir}/{telegram_id}"

        if not os.path.isfile(f'{filename}.session'):
            with open(file=f'{filename}.session', mode='wb') as f:
                f.write(base64.b64decode(session_string.encode('ascii')))

        items.append(Client(
            name=filename,
            api_id=item["appId"],
            api_hash=item["apiHash"],
            app_version=item["sdk"],
            device_model=item["device"],
            lang_code=item["language"],
            system_version=item["appVersion"],
            ipv6=False
        ))

    return items


async def handle_message(self_id: int, chat_id: str, text: str):
    payload = json.dumps({
        "selfId": self_id,
        "chatId": chat_id,
        "text": text
    })

    headers = {
        'ApiKey': settings.bridge_api_key,
        'Content-Type': 'application/json'
    }

    request("POST", f'{url}/api/v1/messages/post',
            headers=headers, data=payload)
