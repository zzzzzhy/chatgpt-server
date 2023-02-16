import requests

data={
    "prompt":"你好,你叫什么名字"
}
headers = {
    "Content-Type": "application/json;charset=utf8"
}
res=requests.post('http://127.0.0.1:8888/ask',json=data,headers=headers)
# res=requests.get('http://127.0.0.1:8888/get_conversations')
print(res.text)