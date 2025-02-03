""" 
Created By SORENSHAMLOU

Create At : 2025/01/02

Update At : 2025/01/03

App Name : Telegram Anonymous Chat

File Name : main.py

Version : 1.0.0
"""
__version__ = "1.0.0"
__author__ = "SORENSHAMLOU"
__date__ = "2025/02/03"
__copyright__ = "Copyright 2025, SORENSHAMLOU"
__credits__ = ["SORENSHAMLOU"]
__license__ = "GPL"


# 0.create a python worker
# 1.create a D1 database and bind it to your worker -> db
# 2.go to D1->the databse->Console and run this sql to create users table
# CREATE TABLE users ("id" integer PRIMARY KEY,"telegram_user_id" text,"rkey" text,"target_user" text)
# 3.open the worker in browser and -> https://yourworker.username.workers.dev/init to set webhook

from js import Object, Response , fetch ,JSON
import hashlib
import json
from pyodide.ffi import to_js as _to_js
import re
import random
import string
import base64

BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
BOT_ID = "BOT_ID"
ALLOWED = "ALL"

HOOK = hashlib.md5(BOT_TOKEN.encode()).hexdigest()

async def on_fetch(request,env):
    db = env.db
    url = request.url
    path = url.split("://", 1)[1].split("/", 1)[1] if "/" in url.split("://", 1)[1] else ""
    base_url = url.rsplit("/", 1)[0]

    if path == "init":

        body = await postReq("setWebhook",{
            "url":f"{base_url}/{HOOK}"
        })

        return Response.new(body)

    if path == HOOK:
        try:     
            tgResponse = (await request.json()).to_py()

            if "callback_query" in tgResponse:
                callbackQuery = tgResponse["callback_query"]
                chatId = callbackQuery["from"]["id"]
                #reply_markup  inline_keyboard callback_data
                #targetReply = await db.prepare("SELECT * FROM users WHERE id = ?").bind(str(chatId)).first()

                replytoID = decrypt(callbackQuery["message"]["reply_markup"]["inline_keyboard"][0][0]["callback_data"])
                targetReply = await db.prepare("SELECT * FROM users WHERE id = ?").bind(str(replytoID)).first()
                await db.prepare("update users set target_user = ? WHERE telegram_user_id = ?").bind(targetReply.telegram_user_id , str(chatId)).run()   


                await postReq("sendMessage",{
                         "chat_id":chatId,
                         "text":"Write and send it down here 👇",
                         "reply_parameters": {
                            "message_id":tgResponse["callback_query"]["message"]["message_id"],
                            "chat_id":chatId
                         }
                        })  

                await postReq("answerCallbackQuery",{
                         "callback_query_id":callbackQuery["id"]
                 })



            if "message" in tgResponse:

                message = tgResponse["message"]
                chatId = message["from"]["id"]

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
    
                if "text" in message and message["text"].startswith("/start"):
    
                    startedUser = await db.prepare("SELECT * FROM users WHERE telegram_user_id = ?").bind(str(chatId)).first()
                    if startedUser:
                        startedUserId = startedUser.id
                    else:
                        startedUser = await db.prepare("INSERT INTO users (telegram_user_id, rkey, target_user) VALUES (?, ?, ?)").bind(str(chatId), rndKey(), "").run()
                        startedUserId = startedUser.meta.last_row_id               
    
    
                    match = re.search(r"/start (\w+)_(\w+)", message["text"])
                    if match:
    
                        param_rkey, param_id = match.groups()
                        targetUser = await db.prepare("SELECT * FROM users WHERE id = ? and rkey = ?").bind(revHxId(param_id) , param_rkey).first()
    
                        if targetUser:
    
                            getChatMember = await postReq("getChatMember",{
                             "chat_id":targetUser.telegram_user_id,
                             "user_id":targetUser.telegram_user_id,
                             })
    
                            await db.prepare("update users set target_user = ? WHERE id = ?").bind(targetUser.telegram_user_id , startedUserId).run()   
                            await postReq("sendMessage",{
                                      "chat_id":chatId,
                                      "text":"Sending an anonymous message to "+str(getChatMember["result"]["user"]["first_name"])+"Hasti, whatever you send will go to them anonymously. You can send text, voice, or anything you want."+"\n Send it down here 👇",
                                      "reply_markup":{"remove_keyboard": True}
                                      })
                        else:
                            await postReq("sendMessage",{
                                      "chat_id":chatId,
                                      "text":"User Not Found!",
                                      "reply_markup":default_keyboard
                                      }) 
    
                    else:
                        await postReq("sendMessage",{
                                      "chat_id":chatId,
                                      "text":"Wellcome",
                                      "reply_markup":default_keyboard
                                      })        
                elif "text" in message and message["text"] == NEWLINK and NEWLINK != "NONE":
    
                    user = await db.prepare("SELECT * FROM users WHERE telegram_user_id = ?").bind(str(chatId)).first()
                    
                    if user:
                        mylink = f"https://t.me/{BOT_ID}?start="+user.rkey+"_"+str(hxId(user.id))
                        await postReq("sendMessage",{
                        "chat_id":chatId,
                        "text":f"Copy and use the link below\n\n Tap on it to copy 👇\n\n`{mylink}`",
                        "parse_mode":"MarkDownV2"
                        })  
                else:
                    
                    me = await db.prepare("SELECT * FROM users WHERE telegram_user_id = ?").bind(str(chatId)).first()
                    
                    if me.target_user:
    
                        await postReq("sendMessage",{
                         "chat_id":me.target_user,
                         "text":"You have a new anonymous message 👇"    
                        })   
                        
                        res = await postReq("copyMessage",{
                         "chat_id":me.target_user,
                         "from_chat_id":chatId,
                         "message_id":message["message_id"],
                         "reply_markup":json.dumps({
                                                    "inline_keyboard": [
                                                    [{"text": "Reply", "callback_data": encrypt(str(me.id))}]
                                                    ]
                                                   })
                                                })

                        if "ok" in res and res["ok"]:
                            await db.prepare("update users set target_user = ? WHERE id = ?").bind("" , me.id).run()
                            await postReq("sendMessage",{
                                      "chat_id":chatId,
                                      "text":"Send successfully",
                                      "reply_markup":default_keyboard
                                      })          
              

        except Exception as e:

            """
            # Debugging: Replace "chat_id" with your own to receive error messages on Telegram
            await postReq("sendMessage",{
            "chat_id":"your-chat-id",  # Replace with your actual chat ID  
            "text":f"err: {e} , {tgResponse}"
            })
            """

        return Response.new("idle")
       
    return Response.new("ok")


def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)

def rndKey():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def hxId(id):
    return (hex(id))[::-1]

def revHxId(hxid):
    return int(hxid[::-1], 16)

def encrypt(data: str) -> str:
    key = HOOK
    return base64.b64encode(bytes([ord(c) ^ ord(key[i % len(key)]) for i, c in enumerate(data)])).decode()

def decrypt(encrypted_data: str) -> str:
    key = HOOK
    decoded = base64.b64decode(encrypted_data)
    return "".join(chr(decoded[i] ^ ord(key[i % len(key)])) for i in range(len(decoded)))



async def postReq(tgMethod, payload):

    options = {
    "body": json.dumps(payload),
    "method": "POST",
        "headers": {
        "content-type": "application/json;charset=UTF-8",
        }
    }

    response = await fetch(f"https://api.telegram.org/bot{BOT_TOKEN}/{tgMethod}",to_js(options))
    body = await response.json()
    JSONBody = body.to_py()
    return JSONBody