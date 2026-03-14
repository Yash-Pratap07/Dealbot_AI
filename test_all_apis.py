"""Comprehensive API test for DealBot AI."""
import urllib.request, json, time, sys

API = "http://127.0.0.1:8000"
results = []


def test(name, method, path, data=None, headers=None):
    h = headers or {}
    if data and isinstance(data, dict):
        h.setdefault("Content-Type", "application/json")
    body = None
    if data:
        if isinstance(data, dict):
            body = json.dumps(data).encode()
        elif isinstance(data, str):
            body = data.encode()
    try:
        req = urllib.request.Request(API + path, data=body, headers=h, method=method)
        r = urllib.request.urlopen(req, timeout=30)
        d = json.loads(r.read())
        results.append((name, r.status, "OK"))
        return d
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:100]
        results.append((name, e.code, msg))
        return None
    except Exception as e:
        results.append((name, 0, str(e)[:100]))
        return None


ts = str(int(time.time()))

# 1. Register
reg = test("Register", "POST", "/auth/register",
           {"username": f"test_{ts}", "email": f"test_{ts}@test.com", "password": "Test@1234"})
token = reg["access_token"] if reg else None
auth = {"Authorization": f"Bearer {token}"} if token else {}

# 2. Login
login_data = f"username=test_{ts}&password=Test%401234"
test("Login", "POST", "/auth/login", login_data,
     headers={"Content-Type": "application/x-www-form-urlencoded"})

# 3. Me
test("Auth/Me", "GET", "/auth/me", headers=auth)

# 4. Deals
test("Deals", "GET", "/deals", headers=auth)

# 5. Chain Status
test("Chain Status", "GET", "/wallet/chain-status")

# 6. Agent Identities
agents = test("Agent Identities", "GET", "/agents/identities")
if agents:
    print(f"  -> {len(agents.get('agents', []))} agents registered")

# 7. Wallet Balance
test("Wallet Balance", "GET", "/wallet/balance?address=0x1234567890abcdef1234567890abcdef12345678")

# 8. Wallet Deals
test("Wallet Deals", "GET", "/wallet/deals", headers=auth)

# 9. Pipeline Search Public
ps = test("Pipeline Search", "GET", "/pipeline/search/public?q=iphone+15&limit=3&currency=INR")
if ps:
    listings = ps.get("listings") or ps.get("results") or []
    print(f"  -> {len(listings)} product listings found")

# 10. Payment Methods
pm = test("Payment Methods", "GET", "/payment/methods")
if pm:
    print(f"  -> {len(pm.get('methods', []))} payment methods")

# 11. Negotiate REST
neg = test("Negotiate REST", "GET",
           "/negotiate?max_price=1000&min_price=500&product=Laptop&market_price=750",
           headers=auth)
if neg:
    print(f"  -> Agreement: {neg.get('agreement')}, Price: {neg.get('final_price')}")
    print(f"  -> Rounds: {neg.get('rounds_taken')}, Settlement: {'Yes' if neg.get('settlement') else 'No'}")

# 12. Analyze Link
al = test("Analyze Link", "POST", "/pipeline/analyze-link",
          {"url": "https://www.amazon.in/dp/B0CHX1W1XY", "limit": 3, "currency": "INR"},
          headers={**auth, "Content-Type": "application/json"})
if al:
    p = al.get("product", {})
    print(f"  -> Product: {p.get('name', '?')[:50]}, Price: {p.get('platform_price', '?')}")

# Summary
print()
print("=" * 70)
title = "API TEST RESULTS"
print(f"{title:^70}")
print("=" * 70)
passed = 0
failed = 0
for name, code, status in results:
    if code == 200:
        icon = "PASS"
        passed += 1
    else:
        icon = "FAIL"
        failed += 1
    print(f"  {icon}  {name:<25} {code:>4}  {status[:50]}")
print("=" * 70)
print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

if failed > 0:
    sys.exit(1)
