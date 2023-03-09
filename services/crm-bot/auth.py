from pyrogram import Client
import session_storage
import base64
from settings import session_dir
import threading
import client_runtime

# async def create_login_request(phone_number: str, api_id: str, api_hash: str):
#     user = TelegramClient(
#         name="sender",
#         api_id=api_id,
#         api_hash=api_hash,
#         phone_number=phone_number,
#         in_memory=True
#     )

#     clients.update({f"{api_id}": user})

#     await user.connect()
#     code = await user.send_code_request(phone=phone_number)

#     return code.phone_code_hash


# async def send_code(code: str, code_hash: str, api_id: str):
#     user: TelegramClient = clients.get(api_id)

#     user.signed_in = await user.sign_in(phone_number=user.phone_number, phone_code_hash=code_hash, phone_code=code)

#     if user.signed_in:
#         user.me = await user.get_me()
#         user.add_handler(MessageHandler(handlers.message_from_user))
#         await session_storage.save_session(user)
#     else:
#         raise Exception('Sign in Error')


async def add_session(telegram_id, session_string: str,
                      app_id, api_hash, phone,
                      sdk, app_version, device, language, proxy):
    filename = f"{session_dir}/{telegram_id}"
    with open(f'{filename}.session', 'wb') as f:
        f.write(base64.b64decode(session_string.encode('ascii')))

    user = Client(
        name=filename,
        api_id=app_id,
        api_hash=api_hash,
        system_version=app_version,
        device_model=device,
        lang_code=language,
        ipv6=False,
        app_version=sdk,
        proxy=proxy
    )

    threading.Thread(target=client_runtime.run, args=[user]).start()

    await session_storage.save_session(
        tg_id=telegram_id,
        session=session_string,
        api_id=app_id,
        api_hash=api_hash,
        phone=phone,
        sdk=sdk,
        app_version=app_version,
        device=device,
        language=language
    )


async def load_sessions():
    sessions = await session_storage.load_sessions()

    for client in sessions:
        try:
            await client_runtime.run(client)

        except Exception as e:
            continue
