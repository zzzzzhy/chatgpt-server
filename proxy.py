"""
Fetches cookies from chat.openai.com and returns them (Flask)
"""
import json
import os
import tls_client
import uvicorn
import sys
import uuid
from os import environ
from os import getenv
from os.path import exists
import requests
from asgiref.wsgi import WsgiToAsgi
from flask import Flask
from flask import jsonify
from flask import request
# from module.cloudflare import get_cookies
# from OpenAIAuth.Cloudflare import Cloudflare
authentication = {}

authentication["cf_clearance"]='4zfY9YkyH2px.YqR36WWP47ulw.kia08_XS8D3ushnc-1676575596-0-1-c9e8a8ec.460421bb.9ee9f70c-250'
authentication["user_agent"]='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:103.0) Gecko/20100101 Firefox/103.0'
# (authentication["user_agent"],authentication["cf_clearance"],)=get_cookies()
GPT_PROXY = os.getenv('GPT_PROXY','')
GPT_HOST = os.getenv('GPT_HOST', '0.0.0.0')
GPT_PORT = int(os.getenv('GPT_PORT', 8888))

app = Flask(__name__)

session = tls_client.Session(client_identifier="firefox_102", )
if GPT_PROXY:
    session.proxies.update(http=GPT_PROXY, https=GPT_PROXY)


context = {"blocked": False}
with open('config.json', encoding="utf-8") as f:
    config = json.load(f)
# Get cloudflare cookies
# (
#     authentication["cf_clearance"],
#     authentication["user_agent"],
# ) = Cloudflare(proxy=GPT_PROXY).get_cf_cookies()


class Error(Exception):
    """Base class for exceptions in this module."""
    source: str
    message: str
    code: int


def __check_fields(data: dict):
    try:
        data["message"]["content"]
    except TypeError:
        return False
    except KeyError:
        return False
    return True


def __check_response(response):
    if response.status_code != 200:
        print(response.text)
        error = Error()
        error.source = "OpenAI"
        error.code = response.status_code
        error.message = response.text
        raise error


def conversation(subpath: str, method: str, data: str):
    if config.get("access_token") is None:
        return jsonify({"error": "Missing access_token"})
    try:
        if context.get("blocked"):
            return jsonify({"error": "Blocking operation in progress"})
        # Get cookies from request
        cookies = {
            "cf_clearance":
            authentication["cf_clearance"],
            "__Secure-next-auth.session-token":
            config.get("session_token"),
        }
        access_token = config.get("access_token")
        # Set user agent
        headers = {
            "Accept": "text/event-stream",
            # "Authorization": "Bearer {access_token}",
            # "User-Agent": authentication["user_agent"],
            "Content-Type": "application/json",
            "X-Openai-Assistant-App-Id": "",
            "Connection": "close",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://chat.openai.com/" + "chat",
        }
        # Send request to OpenAI
        if method == "POST":
            # req = scraper.get(url)
            response = session.post(
                url="https://chat.openai.com/" + subpath,
                headers=headers,
                cookies=cookies,
                data=data,
            )
        elif method == "GET":
            response = session.get(
                url="https://chat.openai.com/" + subpath,
                headers=headers,
                cookies=cookies,
                timeout_seconds=360,
            )
        elif method == "PATCH":
            response = session.patch(
                url="https://chat.openai.com/" + subpath,
                headers=headers,
                cookies=cookies,
                data=data,
                timeout_seconds=360,
            )

        # Check status code
        if response.status_code == 403:
            # Get cf_clearance again
            context["blocked"] = True
            # (
            #     authentication["cf_clearance"],
            #     authentication["user_agent"],
            # ) = Cloudflare(proxy=GPT_PROXY).get_cf_cookies()
            context["blocked"] = False
            # return error
            return jsonify({
                "error": response.status_code,
                "msg": response.text
            })
        # Return response
        print(response.text)
        return response.text
    except Exception as exc:
        return jsonify({"error": str(exc)})


@app.route("/ask", methods=["POST"])
def ask():
    """
    Ask a question to the chatbot
    :param prompt: String
    :param conversation_id: UUID
    :param parent_id: UUID
    :param gen_title: Boolean
    """
    # return request.get_json()
    prompt=request.get_json().get("prompt")
    conversation_id=request.get_json().get("conversation_id",None)
    parent_id=request.get_json().get("parent_id",None)
    gen_title=True,
    if parent_id is not None:
        if conversation_id is None:
            error = Error()
            error.source = "User"
            error.message = "conversation_id must be set once parent_id is set"
            error.code = -1
            raise error
        # user-specified covid and parid, check skipped to avoid rate limit
    else:
        if conversation_id is None:  # new conversation
            parent_id = str(uuid.uuid4())
    data = {
        "action": "next",
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": {"content_type": "text", "parts": [prompt]},
            },
        ],
        "conversation_id": conversation_id,
        "parent_message_id": parent_id,
        "model": "text-davinci-002-render-sha"
        if not config.get("paid")
        else "text-davinci-002-render-paid",
    }
    # new_conv = data["conversation_id"] is None
    response = conversation("api/conversation", "POST", json.dumps(data))
    print(response)
    __check_response(response)
    results=[]
    for line in response.iter_lines():
        line = str(line)[2:-1]
        if line == "" or line is None:
            continue
        if "data: " in line:
            line = line[6:]
        if line == "[DONE]":
            break

        # Replace accidentally escaped double quotes
        line = line.replace('\\"', '"')
        line = line.replace("\\'", "'")
        line = line.replace("\\\\", "\\")
        # Try parse JSON
        try:
            line = json.loads(line)
        except json.decoder.JSONDecodeError:
            continue
        if not __check_fields(line):
            print("Field missing")
            print(line)
            continue
        results.append(line)
        # message = line["message"]["content"]["parts"][0]
        # conversation_id = line["conversation_id"]
        # parent_id = line["message"]["id"]
        # yield {
        #     "message": message,
        #     "conversation_id": conversation_id,
        #     "parent_id": parent_id,
        # }
    return results


@app.route("/get_conversations", methods=["GET"])
def get_conversations():
    """
    Get conversations
    :param offset: Integer
    :param limit: Integer
    """
    offset=0
    limit=20
    response = conversation(
        "api/conversations?offset={offset}&limit={limit}", "GET", None)
    __check_response(response)
    return response
    data = json.loads(response.text)
    return data["items"]


@app.route("/get_msg_history", methods=["GET"])
def get_msg_history(convo_id):
    """
    Get message history
    :param id: UUID of conversation
    """
    response = conversation("api/conversation/{convo_id}", "GET", None)
    __check_response(response)
    data = json.loads(response.text)
    return data


@app.route("/gen_title", methods=["POST"])
def gen_title(convo_id, message_id):
    """
    Generate title for conversation
    """
    data = json.dumps(
        {"message_id": message_id, "model": "text-davinci-002-render"},
    )
    response = conversation(
        "api/conversation/gen_title/{convo_id}", "POST", data)
    __check_response(response)


@app.route("/change_title", methods=["PATCH"])
def change_title(convo_id, title):
    """
    Change title of conversation
    :param id: UUID of conversation
    :param title: String
    """
    data = f'{{"title": "{title}"}}'
    response = conversation("api/conversation/{convo_id}", "PATCH", data)
    __check_response(response)


@app.route("/delete_conversation", methods=["PATCH"])
def delete_conversation(convo_id):
    """
    Delete conversation
    :param id: UUID of conversation
    """
    data = '{"is_visible": false}'
    response = conversation("api/conversation/{convo_id}", "PATCH", data)
    __check_response(response)


@app.route("/clear_conversations", methods=["PATCH"])
def clear_conversations():
    """
    Delete all conversations
    """
    data = '{"is_visible": false}'
    response = conversation("api/conversations", "PATCH", data)
    __check_response(response)


@app.route("/reset_chat", methods=["GET"])
def reset_chat():
    """
    Reset the conversation ID and parent ID.

    :return: None
    """
    res = {
        "conversation_id": None,
        "parent_id": str(uuid.uuid4())
    }
    return json.dumps(res)


# @app.route("/rollback_conversation", methods=["GET"])
# def rollback_conversation(num=1) -> None:
#     """
#     Rollback the conversation.
#     :param num: The number of messages to rollback
#     :return: None
#     """
#     for _ in range(num):
#         self.conversation_id = self.conversation_id_prev_queue.pop()
#         self.parent_id = self.parent_id_prev_queue.pop()


if __name__ == "__main__":
    uvicorn.run(
        WsgiToAsgi(app),
        host=GPT_HOST,
        port=GPT_PORT,
        server_header=False)  # start a high-performance server with Uvicorn
