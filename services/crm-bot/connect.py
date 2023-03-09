from pyrogram import Client

api_id = input('api_id: ')
api_hash = input('api_hash: ')

client = Client('sessions', api_id=api_id, api_hash=api_hash)
client.start()
