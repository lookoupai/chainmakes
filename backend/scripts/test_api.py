"""
测试API是否正常工作
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("Testing ChainMakes API")
print("="*60)

# 1. Test login
print("\n[1] Testing login...")
login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"[OK] Login successful!")
    print(f"     Token: {token[:20]}...")
else:
    print(f"[ERROR] Login failed: {login_response.status_code}")
    print(f"        {login_response.text}")
    exit(1)

# 2. Test get bot list
print("\n[2] Testing get bot list...")
headers = {"Authorization": f"Bearer {token}"}
bots_response = requests.get(
    f"{BASE_URL}/api/v1/bots/",
    headers=headers
)

if bots_response.status_code == 200:
    bots = bots_response.json()
    print(f"[OK] Got {len(bots)} bots")
    for bot in bots:
        print(f"     - Bot ID: {bot['id']}, Name: {bot['bot_name']}, Status: {bot['status']}")
else:
    print(f"[ERROR] Get bots failed: {bots_response.status_code}")
    print(f"        {bots_response.text}")
    exit(1)

# 3. Test get bot detail
if len(bots) > 0:
    bot_id = bots[0]['id']
    print(f"\n[3] Testing get bot detail (ID: {bot_id})...")
    detail_response = requests.get(
        f"{BASE_URL}/api/v1/bots/{bot_id}",
        headers=headers
    )

    if detail_response.status_code == 200:
        print(f"[OK] Got bot detail")
    else:
        print(f"[ERROR] Get detail failed: {detail_response.status_code}")

    # 4. Test get orders
    print(f"\n[4] Testing get orders (Bot ID: {bot_id})...")
    orders_response = requests.get(
        f"{BASE_URL}/api/v1/bots/{bot_id}/orders",
        headers=headers
    )

    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        print(f"[OK] Got {len(orders_data.get('items', []))} orders")
        if 'items' in orders_data and len(orders_data['items']) > 0:
            print(f"     First order: {orders_data['items'][0].get('symbol', 'N/A')}")
    else:
        print(f"[ERROR] Get orders failed: {orders_response.status_code}")
        print(f"        {orders_response.text}")

    # 5. Test get positions
    print(f"\n[5] Testing get positions (Bot ID: {bot_id})...")
    positions_response = requests.get(
        f"{BASE_URL}/api/v1/bots/{bot_id}/positions",
        headers=headers
    )

    if positions_response.status_code == 200:
        positions = positions_response.json()
        print(f"[OK] Got {len(positions)} positions")
        for pos in positions:
            print(f"     - {pos.get('symbol', 'N/A')}: {pos.get('side', 'N/A')}")
    else:
        print(f"[ERROR] Get positions failed: {positions_response.status_code}")

    # 6. Test get spread history
    print(f"\n[6] Testing get spread history (Bot ID: {bot_id})...")
    spread_response = requests.get(
        f"{BASE_URL}/api/v1/bots/{bot_id}/spread-history",
        headers=headers
    )

    if spread_response.status_code == 200:
        spread_data = spread_response.json()
        print(f"[OK] Got {len(spread_data)} spread history points")
    else:
        print(f"[ERROR] Get spread failed: {spread_response.status_code}")

print("\n" + "="*60)
print("API Test Complete!")
print("="*60)
print("\nIf all tests passed, the backend is working correctly.")
print("Please check the frontend console for errors.")
print("="*60 + "\n")
