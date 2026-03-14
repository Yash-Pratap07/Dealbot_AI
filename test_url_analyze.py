"""Quick test script for the analyze-link endpoint."""
import requests
import sys
import os

BASE = "http://localhost:8000"

# Login
login = requests.post(f"{BASE}/auth/login",
    data={"username": "testuser_api", "password": "Test@1234"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test URLs
test_urls = [
    # Full Amazon URL with product name in path
    ("https://www.amazon.in/Apple-iPhone-15-128-GB/dp/B0CHX1W1XY/", "INR"),
    # Samsung on Amazon
    ("https://www.amazon.in/Samsung-Galaxy-S24-Ultra-Titanium/dp/B0CTMDN94Q/", "INR"),
]

for url, currency in test_urls:
    print(f"\n{'='*60}")
    print(f"URL: {url[:70]}...")
    r = requests.post(f"{BASE}/pipeline/analyze-link",
        json={"url": url, "limit": 5, "currency": currency},
        headers=headers, timeout=90)
    d = r.json()
    p = d.get("product", {})
    print(f"Name:         {p.get('name', 'NOT FOUND')}")
    print(f"Price:        {p.get('platform_price')} {p.get('currency')}")
    print(f"Scraped live: {p.get('scraped_live')}")
    print(f"Platform:     {p.get('platform', {}).get('name')}")
    a = d.get("alternatives", {})
    print(f"Alternatives: {a.get('listings_found', 0)} found, {a.get('cheaper_count', 0)} cheaper")
    for lst in a.get("listings", [])[:3]:
        cheaper = "✓ CHEAPER" if lst.get("cheaper_than_original") else ""
        savings = f"  saves {lst.get('currency','')} {lst.get('savings',0):.0f}" if lst.get("savings", 0) > 0 else ""
        print(f"  {lst.get('seller_name','?'):22} {lst.get('currency','')} {lst.get('price',0):>10.2f}  {cheaper}{savings}")
