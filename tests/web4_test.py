import sys, os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)
print('importing orchestrator...')
from orchestrator import run_negotiation, negotiate_stream
print('orchestrator OK')
from blockchain.agent_identity import get_all_agent_identities, AgentRegistry
print('agent_identity OK')
from blockchain.settlement import settle_from_result, _is_chain_available
print('settlement OK')
ids = get_all_agent_identities()
print(f'agents loaded: {len(ids)}')
for a in ids:
    print(f"  {a['type']:20} → {a['address']}")
print('--- ALL WEB4 MODULES OK ---')
