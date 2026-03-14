import sys, os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)
print("1 - starting")
from fastapi import FastAPI
print("2 - fastapi ok")
from database import get_db, User, Deal, init_db
print("3 - database ok")
from auth import hash_password
print("4 - auth ok")  
from blockchain.hash_log import hash_transcript
print("5 - hash_log ok")
from blockchain.contract import generate_contract
print("6 - contract ok")
from orchestrator import run_negotiation, negotiate_stream
print("7 - orchestrator ok")
print("ALL IMPORTS OK")
