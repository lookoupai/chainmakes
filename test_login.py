import requests
import json

url = "http://localhost:8000/api/v1/auth/login"
headers = {"Content-Type": "application/json"}
data = {
    "username": "admin",
    "password": "admin123"
}

print("正在测试登录API...")
print(f"URL: {url}")
print(f"请求数据: {json.dumps(data, indent=2)}")

response = requests.post(url, json=data, headers=headers)

print(f"\n状态码: {response.status_code}")
print(f"响应头: {dict(response.headers)}")
print(f"响应体: {response.text}")

if response.status_code == 200:
    print("\n✅ 登录成功!")
    result = response.json()
    print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
else:
    print(f"\n❌ 登录失败: {response.status_code}")