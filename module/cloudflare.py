from playwright.sync_api import sync_playwright
from cf_clearance import sync_cf_retry, sync_stealth
import requests

# not use cf_clearance, cf challenge is fail
proxies = {
    "all": "socks5://127.0.0.1:7890"
}
res = requests.get('https://chat.openai.com', proxies=proxies)
if '<title>Please Wait... | Cloudflare</title>' in res.text:
    print("cf challenge fail")
# get cf_clearance
with sync_playwright() as p:
    browser = p.firefox.launch(headless=False, proxy={"server": "socks5://127.0.0.1:7890"})
    page = browser.new_page()
    sync_stealth(page, pure=True)
    page.goto('https://chat.openai.com')
    res = sync_cf_retry(page)
    if res:
        cookies = page.context.cookies()
        for cookie in cookies:
            if cookie.get('name') == 'cf_clearance':
                cf_clearance_value = cookie.get('value')
                print(cf_clearance_value)
        ua = page.evaluate('() => {return navigator.userAgent}')
        print(ua)
    else:
        print("cf challenge fail")
    browser.close()
# use cf_clearance, must be same IP and UA
headers = {"user-agent": ua}
cookies = {"cf_clearance": cf_clearance_value}

def get_cookies():
    return ua,cf_clearance_value