# threadagentid

Python SDK for [AgentID](https://github.com/eugene001dayne/agent-id) — cryptographic identity and reputation for AI agents. Part of the Thread Suite.

## Installation

```bash
pip install threadagentid
```

## Quick Start

```python
from agentid import AgentID

aid = AgentID()  # defaults to https://agent-id.onrender.com

# Register
agent = aid.register("my-agent", "my-public-key")
print(agent["credential_hash"])

# Verify
result = aid.verify(agent["agent_id"], "my-public-key")
print(result["verified"])  # True

# Trust lookup
trust = aid.trust_lookup(
    agent_id=agent["agent_id"],
    public_key="my-public-key",
    min_reputation=0.7
)
print(trust["trusted"])         # True or False
print(trust["recommendation"])  # ALLOW or BLOCK

# Update reputation
aid.update_reputation(agent["agent_id"], interaction_success=True)

# Reputation history
history = aid.get_reputation_history(agent["agent_id"])

# Revoke
aid.revoke(agent["agent_id"], reason="Decommissioned.")

# Reactivate
aid.reactivate(agent["agent_id"], "my-public-key", reason="Back online.")

# ChainThread bridge
result = aid.bridge_chainthread(
    chain_id="chain-123",
    sender_id=agent["agent_id"],
    sender_public_key="my-public-key",
    receiver_id="receiver-agent",
    min_reputation=0.7
)
print(result["recommendation"])  # ALLOW or BLOCK
```

## All Methods

```python
aid.health()
aid.register(agent_name, public_key, description)
aid.list_agents(active_only)
aid.get_agent(agent_id)
aid.verify(agent_id, public_key, credential_hash)
aid.revoke(agent_id, reason)
aid.reactivate(agent_id, public_key, reason)
aid.get_reputation(agent_id)
aid.update_reputation(agent_id, interaction_success, violation, pii_incident, detail)
aid.get_reputation_history(agent_id)
aid.get_history(agent_id)
aid.trust_lookup(agent_id, public_key, querying_agent, min_reputation)
aid.list_trust_lookups(limit)
aid.bridge_chainthread(chain_id, sender_id, sender_public_key, receiver_id, min_reputation)
aid.bridge_status()
aid.stats()
```

## Links

- GitHub: https://github.com/eugene001dayne/agent-id
- API Docs: https://agent-id.onrender.com/docs
- Thread Suite: https://github.com/eugene001dayne