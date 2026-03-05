import hashlib
import json


def generate_contract(final_price, history):

    transcript = json.dumps(history)
    hash_value = hashlib.sha256(transcript.encode()).hexdigest()

    contract = {
        "price": final_price,
        "hash": hash_value,
        "status": "Pending Approval"
    }

    return contract
