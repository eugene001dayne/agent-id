# threadagentid

JavaScript SDK for [AgentID](https://github.com/eugene001dayne/agent-id) — cryptographic identity and reputation for AI agents. Part of the Thread Suite.

## Installation

```bash
npm install threadagentid
```

## Quick Start

```javascript
const AgentID = require("threadagentid");
const aid = new AgentID(); // defaults to https://agent-id.onrender.com

// Register
const agent = await aid.register("my-agent", "my-public-key");
console.log(agent.credential_hash);

// Verify
const result = await aid.verify(agent.agent_id, "my-public-key");
console.log(result.verified); // true

// Trust lookup
const trust = await aid.trustLookup(
  agent.agent_id,
  "my-public-key",
  "receiver-agent",
  0.7
);
console.log(trust.trusted);         // true or false
console.log(trust.recommendation);  // ALLOW or BLOCK

// Update reputation
await aid.updateReputation(agent.agent_id, true, false, false);

// Revoke
await aid.revoke(agent.agent_id, "Decommissioned.");

// Reactivate
await aid.reactivate(agent.agent_id, "my-public-key", "Back online.");

// ChainThread bridge
const bridge = await aid.bridgeChainthread(
  "chain-123",
  agent.agent_id,
  "my-public-key",
  "receiver-agent",
  0.7
);
console.log(bridge.recommendation); // ALLOW or BLOCK
```

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
- API Docs: https://agent-id.onrender.com/docs
- Thread Suite: https://github.com/eugene001dayne