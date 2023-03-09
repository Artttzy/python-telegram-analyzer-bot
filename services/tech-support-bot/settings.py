import os
from dotenv import load_dotenv
load_dotenv()

CHANNEL_ID = os.getenv('CHANNEL_ID')
CALL_CENTER_ID = os.getenv('CALL_CENTER_ID')
CHANNEL_LINK = '146.0.78.143:5001'
BOT_TOKEN = os.getenv('BOT_TOKEN')