# AgentID

Cryptographic identity and reputation for AI agents. Part of the [Thread Suite](https://github.com/eugene001dayne).

Every AI agent gets a verifiable identity and a track record. When two agents meet, they present credentials. Trust is earned, not assumed.

## The Problem

In multi-agent systems, agents interact with other agents constantly. Right now there is no standard for agent identity. An `agent_id` is just a string. There is no way to verify who an agent is, what its history is, or whether it has a track record of reliable behavior. AgentID fixes this.

## What It Does

- **Credential issuance** — register any AI agent and receive a cryptographically signed credential
- **Credential verification** — verify any agent's identity using their public key and credential hash
- **Reputation scoring** — every agent builds a track record across interactions, violations, and PII incidents
- **Trust lookup** — one call returns a full trust decision: credential valid, reputation score, and a binary trusted flag
- **Revocation** — compromised or decommissioned agents can be revoked instantly; all future lookups return trusted: false
- **ChainThread bridge** — AgentID integrates directly with ChainThread to verify sender identity before handoff envelopes are accepted

## The Thread Suite
Iron-Thread          → Did the AI return the right structure?
TestThread           → Did the agent do the right thing?
PromptThread         → Is my prompt the best version of itself?
ChainThread          → Did the handoff between agents succeed?
PolicyThread         → Is the AI staying within our rules in production?
ThreadWatch          → Is the entire pipeline healthy right now?
Behavioral Fingerprint → Has this agent's behavior changed?
AgentID              → Who is this agent and can we trust it?

## Live

| Resource | URL |
|----------|-----|
| API | https://agent-id.onrender.com |
| API Docs | https://agent-id.onrender.com/docs |
| Dashboard | https://agent-id-dashboard.lovable.app |
| PyPI | pip install threadagentid |
| npm | npm install threadagentid |

## Quick Start

```python
from agentid import AgentID

aid = AgentID()

# Register an agent
agent = aid.register(
    agent_name="research-agent-v1",
    public_key="your-public-key",
    description="Primary research agent"
)

print(agent["agent_id"])        # agent-uuid
print(agent["credential_hash"]) # sha256 hash — store this

# Verify identity
result = aid.verify(agent["agent_id"], "your-public-key")
print(result["verified"])       # True

# Trust lookup — one call, full decision
trust = aid.trust_lookup(
    agent_id=agent["agent_id"],
    public_key="your-public-key",
    querying_agent="receiver-agent",
    min_reputation=0.7
)
print(trust["trusted"])         # True or False
print(trust["recommendation"])  # ALLOW or BLOCK

# Update reputation after an interaction
aid.update_reputation(
    agent["agent_id"],
    interaction_success=True,
    violation=False,
    pii_incident=False
)

# Revoke a compromised agent
aid.revoke(agent["agent_id"], reason="Compromised during audit.")
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /agents | Register agent, issue credential |
| GET | /agents | List all agents |
| GET | /agents/{id} | Get agent with reputation |
| POST | /agents/{id}/verify | Verify credential |
| POST | /agents/{id}/revoke | Revoke credential |
| POST | /agents/{id}/reactivate | Reactivate credential |
| GET | /agents/{id}/reputation | Get reputation record |
| POST | /agents/{id}/reputation/update | Submit interaction outcome |
| GET | /agents/{id}/reputation/history | Full score history |
| GET | /agents/{id}/history | Full credential event history |
| POST | /trust/lookup | One-call trust decision |
| GET | /trust/lookups | List all trust lookup records |
| POST | /bridge/chainthread | ChainThread handoff verification |
| GET | /bridge/status | Thread Suite health check |
| GET | /dashboard/stats | Overview statistics |

## Reputation Score

Scores run from 0.0 to 1.0. Every agent starts at 1.0.

| Grade | Score | Meaning |
|-------|-------|---------|
| A | ≥ 0.9 | Highly trusted |
| B | ≥ 0.75 | Trusted |
| C | ≥ 0.6 | Acceptable |
| D | ≥ 0.4 | Poor — review before accepting |
| F | < 0.4 | Do not trust |

Formula: `base_rate - (violations × 0.02) - (pii_incidents × 0.05)`

## ChainThread Integration

When ChainThread processes a handoff envelope, it calls AgentID to verify the sender before the envelope is accepted:

```python
result = aid.bridge_chainthread(
    chain_id="chain-abc123",
    sender_id="agent-uuid",
    sender_public_key="sender-public-key",
    receiver_id="receiver-agent-uuid",
    min_reputation=0.7
)

print(result["recommendation"])  # ALLOW or BLOCK
print(result["trusted"])         # True or False
```

## Environment Variables
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

## Self-Hosting

```bash
git clone https://github.com/eugene001dayne/agent-id
cd agent-id
pip install -r requirements.txt
# add .env with SUPABASE_URL and SUPABASE_KEY
python -m uvicorn main:app --reload
```

## License

Apache 2.0

---

*Built by Eugene Dayne Mawuli — Thread Suite: Iron-Thread · TestThread · PromptThread · ChainThread · PolicyThread · ThreadWatch · Behavioral Fingerprint · AgentID*

*"Built for the age of AI agents."*