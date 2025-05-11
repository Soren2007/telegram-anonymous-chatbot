""" 
Created By SORENSHAMLOU

Create At : 2025/01/02

Update At : 2025/01/03

App Name : Telegram Anonymous Chat

File Name : main.py

Version : 1.0.0
"""
__version__ = "1.0.0"  # Defines the version of the script
__author__ = "SORENSHAMLOU"  # Author of the script
__date__ = "2025/02/03"  # Date of last modification
__copyright__ = "Copyright 2025, SORENSHAMLOU"  # Copyright notice
__credits__ = ["SORENSHAMLOU"]  # Credits for contributors
__license__ = "GPL"  # License type

# Steps for setting up the worker and database
# 0. Create a Python-based worker
# 1. Create a D1 database and bind it to the worker (referred to as `db`)
# 2. Go to D1 -> the database -> Console and execute SQL to create a `users` table:
#    CREATE TABLE users ("id" integer PRIMARY KEY,"telegram_user_id" text,"rkey" text,"target_user" text)
# 3. Open the worker in a browser and access `https://yourworker.username.workers.dev/init` to set the webhook

from js import Object, Response, fetch, JSON  # Import JavaScript bindings for Pyodide
import hashlib  # Import for hashing functions
import json  # JSON handling
from pyodide.ffi import to_js as _to_js  # Conversion function for JS integration
import re  # Regular expression module for pattern matching
import random  # Random module for generating values
import string  # String module for character manipulation
import base64  # Encoding and decoding base64

# Telegram bot credentials
BOT_TOKEN = "TELEGRAM_BOT_TOKEN"  # Token for the Telegram bot
BOT_ID = "BOT_ID"  # Telegram bot ID
ALLOWED = "ALL"  # Access control setting

# Generate a hash of the bot token (used for webhook verification)
HOOK = hashlib.md5(BOT_TOKEN.encode()).hexdigest()

# Main handler function for requests
async def on_fetch(request, env):
    db = env.db  # Reference to the database
    url = request.url  # Get request URL
    path = url.split("://", 1)[1].split("/", 1)[1] if "/" in url.split("://", 1)[1] else ""  # Extract path
    base_url = url.rsplit("/", 1)[0]  # Get base URL

    # Initialize webhook
    if path == "init":
        body = await postReq("setWebhook", {
            "url": f"{base_url}/{HOOK}"  # Set webhook endpoint
        })
        return Response.new(body)

    # Handle webhook callbacks
    if path == HOOK:
        try:
            tgResponse = (await request.json()).to_py()  # Convert incoming JSON request to Python dict

            # Handle callback queries
            if "callback_query" in tgResponse:
                callbackQuery = tgResponse["callback_query"]
                chatId = callbackQuery["from"]["id"]  # Extract sender ID
                
                # Extract reply data from inline keyboard callback
                replytoID = decrypt(callbackQuery["message"]["reply_markup"]["inline_keyboard"][0][0]["callback_data"])
                targetReply = await db.prepare("SELECT * FROM users WHERE id = ?").bind(str(replytoID)).first()
                
                # Update target user for reply
                await db.prepare("update users set target_user = ? WHERE telegram_user_id = ?").bind(targetReply.telegram_user_id, str(chatId)).run()  

                # Prompt user to send a message
                await postReq("sendMessage", {
                    "chat_id": chatId,
                    "text": "Write and send it down here 👇",
                    "reply_parameters": {
                        "message_id": tgResponse["callback_query"]["message"]["message_id"],
                        "chat_id": chatId
                    }
                })

                # Confirm callback query response
                await postReq("answerCallbackQuery", {
                    "callback_query_id": callbackQuery["id"]
                })

            # Handle incoming messages
            if "message" in tgResponse:
                message = tgResponse["message"]
                chatId = message["from"]["id"]  # Extract sender ID

                # Define user access
                if str(ALLOWED).lower() == "all" or message["from"]["username"] in ALLOWED:
                    NEWLINK = "Create an anonymous link for me✅"
                    default_keyboard = {
                        "keyboard": [
                            [{"text": NEWLINK}]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": True
                    }
                else:
                    default_keyboard = {}
                    NEWLINK = "NONE"

                # Handle /start command
                if "text" in message and message["text"].startswith("/start"):
                    startedUser = await db.prepare("SELECT * FROM users WHERE telegram_user_id = ?").bind(str(chatId)).first()
                    
                    # If user exists, retrieve their ID, otherwise create a new user entry
                    if startedUser:
                        startedUserId = startedUser.id
                    else:
                        startedUser = await db.prepare("INSERT INTO users (telegram_user_id, rkey, target_user) VALUES (?, ?, ?)").bind(str(chatId), rndKey(), "").run()
                        startedUserId = startedUser.meta.last_row_id  

                    # Parse parameters from the /start command
                    match = re.search(r"/start (\w+)_(\w+)", message["text"])
                    if match:
                        param_rkey, param_id = match.groups()
                        targetUser = await db.prepare("SELECT * FROM users WHERE id = ? and rkey = ?").bind(revHxId(param_id), param_rkey).first()
                        
                        if targetUser:
                            getChatMember = await postReq("getChatMember", {
                                "chat_id": targetUser.telegram_user_id,
                                "user_id": targetUser.telegram_user_id,
                            })

                            await db.prepare("update users set target_user = ? WHERE id = ?").bind(targetUser.telegram_user_id, startedUserId).run()
                            await postReq("sendMessage", {
                                "chat_id": chatId,
                                "text": f"Sending an anonymous message to {getChatMember['result']['user']['first_name']}. Send your message here 👇",
                                "reply_markup": {"remove_keyboard": True}
                            })
                        else:
                            await postReq("sendMessage", {
                                "chat_id": chatId,
                                "text": "User Not Found!",
                                "reply_markup": default_keyboard
                            })

                    else:
                        await postReq("sendMessage", {
                            "chat_id": chatId,
                            "text": "Welcome",
                            "reply_markup": default_keyboard
                        })

                # Generate an anonymous link for the user
                elif "text" in message and message["text"] == NEWLINK and NEWLINK != "NONE":
                    user = await db.prepare("SELECT * FROM users WHERE telegram_user_id = ?").bind(str(chatId)).first()
                    
                    if user:
                        # Create a unique anonymous link for the user
                        mylink = f"https://t.me/{BOT_ID}?start=" + user.rkey + "_" + str(hxId(user.id))
                        
                        # Send the generated link to the user
                        await postReq("sendMessage", {
                            "chat_id": chatId,
                            "text": f"Copy and use the link below\n\n Tap on it to copy 👇\n\n`{mylink}`",
                            "parse_mode": "MarkDownV2"
                        })  

                else:
                    # Retrieve the sender's information from the database
                    me = await db.prepare("SELECT * FROM users WHERE telegram_user_id = ?").bind(str(chatId)).first()
                    
                    if me.target_user:
                        # Notify the recipient that they have received an anonymous message
                        await postReq("sendMessage", {
                            "chat_id": me.target_user,
                            "text": "You have a new anonymous message 👇"    
                        })   
                        
                        # Forward the anonymous message to the target user
                        res = await postReq("copyMessage", {
                            "chat_id": me.target_user,
                            "from_chat_id": chatId,
                            "message_id": message["message_id"],
                            "reply_markup": json.dumps({
                                "inline_keyboard": [
                                    [{"text": "Reply", "callback_data": encrypt(str(me.id))}]
                                ]
                            })
                        })

                        # If message forwarding is successful, update the database and send confirmation
                        if "ok" in res and res["ok"]:
                            await db.prepare("update users set target_user = ? WHERE id = ?").bind("", me.id).run()
                            await postReq("sendMessage", {
                                "chat_id": chatId,
                                "text": "Send successfully",
                                "reply_markup": default_keyboard
                            })          

        except Exception as e:
            """
            # Debugging: Send error details to a specified Telegram chat
            await postReq("sendMessage", {
                "chat_id": "your-chat-id",  # Replace with your actual chat ID  
                "text": f"err: {e} , {tgResponse}"
            })
            """
        return Response.new("idle")

    return Response.new("ok")

# Function to convert Python objects to JavaScript-compatible objects
def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)

# Function to generate a random key
def rndKey():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Function to obfuscate an ID using hex encoding
def hxId(id):
    return (hex(id))[::-1]

# Function to reverse hex encoding and retrieve the original ID
def revHxId(hxid):
    return int(hxid[::-1], 16)

# Function to encrypt data using XOR with a secret key
def encrypt(data: str) -> str:
    key = HOOK  # Use the hashed bot token as a secret key
    return base64.b64encode(bytes([ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(data)])).decode()

# Function to decrypt encrypted data using XOR with the secret key
def decrypt(encrypted_data: str) -> str:
    key = HOOK  # Use the hashed bot token as a secret key
    decoded = base64.b64decode(encrypted_data)
    return "".join(chr(decoded[i] ^ ord(key[i % len(key)])) for i in range(len(decoded)))

# Function to send POST requests to the Telegram API
async def postReq(tgMethod, payload):
    options = {
        "body": json.dumps(payload),
        "method": "POST",
        "headers": {
            "content-type": "application/json;charset=UTF-8",
        }
    }

    # Send the request and retrieve the response
    response = await fetch(f"https://api.telegram.org/bot{BOT_TOKEN}/{tgMethod}", to_js(options))
    body = await response.json()
    JSONBody = body.to_py()
    return JSONBody
