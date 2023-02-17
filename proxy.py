"""
Fetches cookies from chat.openai.com and returns them (Flask)
"""
import json
import os
import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Flask
from flask import request
from revChatGPT.V1 import Chatbot

app = Flask(__name__)

with open('config.json', encoding="utf-8") as f:
    config = json.load(f)

chatbot=Chatbot(config)

@app.route("/ask", methods=["POST"])
def ask():
    res={}
    prompt=request.get_json().get("prompt",None)
    conversation_id=request.get_json().get("conversation_id",None)
    parent_id=request.get_json().get("parent_id",None)
    if prompt is not None:
        for data in chatbot.ask(prompt=prompt,parent_id=parent_id,conversation_id=conversation_id):
            res=data
    else:
        res={"msg":"prompt cannot be none"}
    return json.dumps(res)

@app.route("/get_conversations", methods=["GET"])
def get_conversations():
    offset=request.get_json().get("offset",0)
    limit=request.get_json().get("limit",20)
    res=chatbot.get_conversations(offset=offset, limit=limit)
    return json.dumps(res)

@app.route("/get_msg_history", methods=["GET"])
def get_msg_history():
    convo_id=request.get_json().get("conversation_id",None)
    if convo_id is None:
        return json.dumps({"msg":"conversation_id cannot be none"})
        
    res=chatbot.get_msg_history(convo_id)
    return json.dumps(res)

@app.route("/change_title", methods=["PATCH"])
def change_title():
    title=request.get_json().get("title",None)
    convo_id=request.get_json().get("conversation_id",None)
    if convo_id is None:
        return json.dumps({"msg":"conversation_id cannot be none"})
    res=chatbot.change_title(convo_id,title)
    return json.dumps(res)

@app.route("/delete_conversation", methods=["PATCH"])
def delete_conversation():
    convo_id=request.get_json().get("conversation_id",None)
    if convo_id is None:
        return json.dumps({"msg":"conversation_id cannot be none"})
    chatbot.delete_conversation(convo_id)
    return '{"msg":"success"}'


@app.route("/clear_conversations", methods=["PATCH"])
def clear_conversations():
    chatbot.clear_conversations()
    return '{"msg":"success"}'

GPT_HOST = os.getenv('GPT_HOST', '0.0.0.0')
GPT_PORT = int(os.getenv('GPT_PORT', 8888))
if __name__ == "__main__":
    uvicorn.run(
        WsgiToAsgi(app),
        host=GPT_HOST,
        port=GPT_PORT,
        server_header=False)  # start a high-performance server with Uvicorn
