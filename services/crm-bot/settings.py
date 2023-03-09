from dotenv import load_dotenv
import os
load_dotenv()

bridge_api_key = os.getenv('BRIDGE_API_KEY')
session_dir = os.getenv('SESSION_DIR')
secret_key = os.getenv('SECRET_KEY')
