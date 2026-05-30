# threadagentid

JavaScript SDK for [AgentID](https://github.com/eugene001dayne/agent-id) — cryptographic identity and reputation for AI agents. Part of the [Thread Suite](https://github.com/eugene001dayne).

## Installation

```bash
npm install threadagentid
```

## What It Does

Every AI agent gets a verifiable identity and a track record. When two agents meet, they present credentials. Trust is earned, not assumed.

New agents start at **0.5 (grade C — provisionally trusted)**. Full trust requires 10 verified interactions. An agent cannot exceed a reputation score of 0.8 until it has accumulated a track record.

## Quick Start

```javascript
const AgentID = require("threadagentid");
const aid = new AgentID(); // defaults to https://agent-id.onrender.com

// Register — new agents start at 0.5, grade C
const agent = await aid.register("my-agent", "my-public-key");
console.log(agent.reputation_score);      // 0.5
console.log(agent.grade);                 // C
console.log(agent.verified_interactions); // 0
console.log(agent.trust_ceiling);         // 0.8
console.log(agent.credential_hash);       // store this

// Verify identity
const result = await aid.verify(agent.agent_id, "my-public-key");
console.log(result.verified);             // true

// Trust lookup — one call, full decision
const trust = await aid.trustLookup(
  agent.agent_id,
  "my-public-key",
  "receiver-agent",
  0.7
);
console.log(trust.trusted);              // true or false
console.log(trust.recommendation);       // ALLOW or BLOCK
console.log(trust.trust_ceiling_active); // true until 10 verified interactions

// Update reputation
// A verified interaction = success + no violation + no PII incident
await aid.updateReputation(
  agent.agent_id,
  true,   // interaction_success
  false,  // violation
  false,  // pii_incident
  "Completed handoff successfully"
);

// Get full reputation record
const rep = await aid.getReputation(agent.agent_id);
console.log(rep.verified_interactions);  // how many clean interactions
console.log(rep.trust_ceiling_active);   // false once >= 10 verified

// Revoke
await aid.revoke(agent.agent_id, "Compromised.");

// Reactivate
await aid.reactivate(agent.agent_id, "my-public-key", "Cleared.");

// ChainThread bridge
const bridge = await aid.bridgeChainthread(
  "chain-123",
  agent.agent_id,
  "my-public-key",
  "receiver-agent",
  0.7
);
console.log(bridge.recommendation);      // ALLOW or BLOCK
console.log(bridge.trust_ceiling_active);
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

Trust ceiling: agents with fewer than 10 verified interactions cannot exceed 0.8.

## All Methods

```javascript
aid.health()
aid.register(agentName, publicKey, description)
aid.listAgents(activeOnly)
aid.getAgent(agentId)
aid.verify(agentId, publicKey, credentialHash)
aid.revoke(agentId, reason)
aid.reactivate(agentId, publicKey, reason)
aid.getReputation(agentId)
aid.updateReputation(agentId, interactionSuccess, violation, piiIncident, detail)
aid.getReputationHistory(agentId)
aid.getHistory(agentId)
aid.trustLookup(agentId, publicKey, queryingAgent, minReputation)
aid.listTrustLookups(limit)
aid.bridgeChainthread(chainId, senderId, senderPublicKey, receiverId, minReputation)
aid.bridgeStatus()
aid.stats()
```

## Links

- GitHub: https://github.com/eugene001dayne/agent-id
- Live API: https://agent-id.onrender.com
- API Docs: https://agent-id.onrender.com/docs
- Thread Suite: https://github.com/eugene001dayne