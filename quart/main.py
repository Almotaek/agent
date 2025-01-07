from Agent import Agent
from quart import Quart, request, jsonify
from quart_cors import cors
import json
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import logging

# Getting env keys
load_dotenv("../.env")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = os.getenv("VERSION")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Quart app settings
app = Quart(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# app.config['PROVIDE_AUTOMATIC_OPTIONS'] = True

agent = Agent()

def get_text_message_input(recipient, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    })

async def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as response:
            if response.status == 200:
                logger.info(f"Status: {response.status}")
                logger.info(f"Content-type: {response.headers['content-type']}")
                response_text = await response.text()
                logger.info(f"Body: {response_text}")
                return response
            else:
                logger.error(f"Error {response.status}: {await response.text()}")
                return response

@app.route('/webhook', methods=['GET', 'POST'])
async def webhook():
    if request.method == 'POST':
        logger.info(f"its working alhamdulillah")
        data = await request.get_json()
        message = data.get('message', 'No message content')
        sender = data.get('from', 'Unknown sender')
        logger.info(f"Message received from {sender}")
        
        gpt_response = await agent.send_message(sender, message)
        message_data = get_text_message_input(recipient=RECIPIENT_WAID, text=gpt_response)
        await send_message(message_data)
        
        return jsonify({"status": "success"}), 200
    else:
        return "Quart webhook endpoint is working", 200

@app.route('/', methods=['GET'])
async def home():
    return "Quart app is running", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)