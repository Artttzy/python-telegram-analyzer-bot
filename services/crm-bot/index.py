from aioflask import Flask, request, Response
from util import get_or_create_eventloop
from client_runtime import send_message as send_from_telethon
from pyrogram.methods.utilities.idle import idle
from settings import secret_key
import auth
import threading

app = Flask(__name__)


# @app.route("/request_code", methods=['POST'])
# async def request_code():
#     try:
#         try:
#             phone_number = request.args.get('phone')
#             api_id = request.args.get('api_id')
#             api_hash = request.args.get('api_hash')
#         except Exception:
#             phone_number = None
#             api_id = None
#             api_hash = None

#         if phone_number is None or api_hash is None or api_id is None:
#             return Response(
#                 response="missing field",
#                 status=400,
#                 content_type="application/json"
#             )

#         code_hash = await auth.create_login_request(phone_number=phone_number, api_id=api_id, api_hash=api_hash)
#         return jsonify(codeHash=code_hash)
#     except Exception as e:
#         return app.response_class(status=500, response=json.dumps(str(e)))


# @app.route("/submit_code", methods=['POST'])
# async def submit_code():
#     try:
#         try:
#             phone_number = request.args.get('phone')
#             code_hash = request.args.get('code_hash')
#             code = request.args.get('code')
#             api_id = request.args.get('api_id')
#             api_hash = request.args.get('api_hash')
#         except Exception:
#             phone_number = None
#             code_hash = None
#             code = None
#             api_id = None
#             api_hash = None

#         if phone_number is None or code_hash is None or code is None or api_id is None or api_hash is None:
#             return Response(
#                 response="missing required fields",
#                 status=400,
#                 content_type="application/json"
#             )

#         await auth.send_code(code=code, code_hash=code_hash, api_id=api_id)
#         return Response(status=200, response="Login succeeded")

#     except Exception as e:
#         return app.response_class(status=500, response=json.dumps(str(e)))


@app.route("/add_session", methods=['POST'])
async def add_session():
    args = request.args
    telegram_id = args.get('telegram_id')
    session_string = args.get('session_string')
    app_id = args.get('app_id')
    api_hash = args.get('api_hash')
    phone = args.get('phone')
    sdk = args.get('sdk')
    app_version = args.get('app_version')
    device = args.get('device')
    language = args.get('language')

    await auth.add_session(telegram_id,
                           session_string,
                           app_id,
                           api_hash,
                           phone,
                           sdk,
                           app_version,
                           device,
                           language,
                           None)

    return Response(status=200)


@app.route("/send_message", methods=['POST'])
async def send_message():
    secret = request.headers.get('ApiSecret')

    if secret != secret_key:
        return Response(status=401)

    args = request.args
    from_id = int(args.get('from'))
    to_id = args.get('to')
    message = args.get('message')

    await send_from_telethon(from_id=from_id, to_id=to_id, message=message)
    return Response(status=200)


if __name__ == "__main__":
    loop = get_or_create_eventloop()
    loop.run_until_complete(auth.load_sessions())
    threading.Thread(target=app.run, args=["0.0.0.0", 5284]).start()
    idle()
