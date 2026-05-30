# threadagentid

Python SDK for [AgentID](https://github.com/eugene001dayne/agent-id) — cryptographic identity and reputation for AI agents. Part of the [Thread Suite](https://github.com/eugene001dayne).

## Installation

```bash
pip install threadagentid
```

## What It Does

Every AI agent gets a verifiable identity and a track record. When two agents meet, they present credentials. Trust is earned, not assumed.

New agents start at **0.5 (grade C — provisionally trusted)**. Full trust requires 10 verified interactions. An agent cannot exceed a reputation score of 0.8 until it has accumulated a track record.

## Quick Start

```python
from agentid import AgentID

aid = AgentID()  # defaults to https://agent-id.onrender.com

# Register — new agents start at 0.5, grade C
agent = aid.register("my-agent", "my-public-key")
print(agent["reputation_score"])      # 0.5
print(agent["grade"])                 # C
print(agent["verified_interactions"]) # 0
print(agent["trust_ceiling"])         # 0.8
print(agent["credential_hash"])       # store this

# Verify identity
result = aid.verify(agent["agent_id"], "my-public-key")
print(result["verified"])             # True

# Trust lookup — one call, full decision
trust = aid.trust_lookup(
    agent_id=agent["agent_id"],
    public_key="my-public-key",
    querying_agent="receiver-agent",
    min_reputation=0.7
)
print(trust["trusted"])              # True or False
print(trust["recommendation"])       # ALLOW or BLOCK
print(trust["trust_ceiling_active"]) # True until 10 verified interactions

# Update reputation after an interaction
# A verified interaction = success + no violation + no PII incident
aid.update_reputation(
    agent["agent_id"],
    interaction_success=True,
    violation=False,
    pii_incident=False,
    detail="Completed handoff successfully"
)

# Get reputation with full track record detail
rep = aid.get_reputation(agent["agent_id"])
print(rep["verified_interactions"])   # how many clean interactions
print(rep["trust_ceiling_active"])    # False once ≥ 10 verified

# Reputation history
history = aid.get_reputation_history(agent["agent_id"])

# Revoke a compromised agent
aid.revoke(agent["agent_id"], reason="Compromised during audit.")

# Reactivate with proof of ownership
aid.reactivate(agent["agent_id"], "my-public-key", reason="Cleared.")

# ChainThread bridge — verify before accepting a handoff
result = aid.bridge_chainthread(
    chain_id="chain-abc123",
    sender_id=agent["agent_id"],
    sender_public_key="my-public-key",
    receiver_id="receiver-agent",
    min_reputation=0.7
)
print(result["recommendation"])      # ALLOW or BLOCK
print(result["trust_ceiling_active"])

# Thread Suite health
aid.bridge_status()
aid.stats()
```

## Trust and Reputation Model

| Grade | Score | Verified Interactions | Meaning |
|-------|-------|-----------------------|---------|
| A | ≥ 0.9 | ≥ 10 | Fully trusted, proven track record |
| B | ≥ 0.75 | ≥ 10 | Trusted, proven track record |
| C | ≥ 0.6 | any | Acceptable, may be unproven |
| D | ≥ 0.4 | any | Poor — review before accepting |
| F | < 0.4 | any | Do not trust |

Score formula: `base_rate - (violations × 0.02) - (pii_incidents × 0.05)`

Trust ceiling: agents with fewer than 10 verified interactions cannot exceed 0.8, regardless of math.

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
- Live API: https://agent-id.onrender.com
- API Docs: https://agent-id.onrender.com/docs
- Thread Suite: https://github.com/eugene001dayne