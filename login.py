import json
import logging
import requests
import sys
from OpenAIAuth.OpenAIAuth import OpenAIAuth

# Disable all logging
logging.basicConfig(level=logging.ERROR)

class Chatbot:
    """
    Chatbot class for ChatGPT
    """

    def __init__(
        self,
        config,
    ) -> None:
        self.config = config
        self.session = requests.Session()
        if "proxy" in config:
            if isinstance(config["proxy"], str) is False:
                raise Exception("Proxy must be a string!")
            proxies = {
                "http": config["proxy"],
                "https": config["proxy"],
            }
            self.session.proxies.update(proxies)
        if "verbose" in config:
            if type(config["verbose"]) != bool:
                raise Exception("Verbose must be a boolean!")
            self.verbose = config["verbose"]
        else:
            self.verbose = False
        if "email" in config and "password" in config:
            pass
        elif "session_token" in config:
            pass
        elif "access_token" in config:
            self.__refresh_headers(config["access_token"])
        else:
            raise Exception("No login details provided!")
        if "access_token" not in config:
            self.__login()

    def __refresh_headers(self, access_token):
        self.session.headers.clear()
        self.session.headers.update(
            {
                "Accept": "text/event-stream",
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Openai-Assistant-App-Id": "",
                "Connection": "close",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://chat.openai.com/chat",
            },
        )

    def __login(self):
        if ("email" not in self.config or "password" not in self.config) and "session_token" not in self.config:
            raise Exception("No login details provided!")
        print(self.config.get("proxy"))
        auth = OpenAIAuth(
            email_address=self.config.get("email"),
            password=self.config.get("password"),
            proxy=self.config.get("proxy"),
            debug=True
        )
        if self.config.get("session_token"):
            auth.session_token = self.config["session_token"]
            auth.get_access_token()
            if auth.access_token is None:
                del self.config["session_token"]
                self.__login()
                return
        else:
            auth.begin()
            self.config["session_token"] = auth.session_token
            auth.get_access_token()
        if auth.access_token:
            self.__refresh_headers(auth.access_token)
            self.config["access_token"] = auth.access_token
            self.config.remove("email")
            self.config.remove("password")
            with open('config.json','w') as f:
                f.write(json.dumps(self.config))
            sys.exit(200)

if __name__ == '__main__':
    with open("login.json", encoding="utf-8") as f:
        config = json.load(f)
    Chatbot(config)
