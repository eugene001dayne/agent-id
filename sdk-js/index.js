const fetch = require("node-fetch");

class AgentID {
  constructor(baseUrl = "https://agent-id.onrender.com") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async _request(method, path, body = null) {
    const options = {
      method,
      headers: { "Content-Type": "application/json" }
    };
    if (body) options.body = JSON.stringify(body);
    const res = await fetch(`${this.baseUrl}${path}`, options);
    if (!res.ok) {
      throw new Error(`AgentID error: ${res.status} ${await res.text()}`);
    }
    return res.json();
  }

  health() {
    return this._request("GET", "/health");
  }

  register(agentName, publicKey, description = null) {
    return this._request("POST", "/agents", {
      agent_name: agentName,
      public_key: publicKey,
      description
    });
  }

  listAgents(activeOnly = true) {
    return this._request("GET", `/agents?active_only=${activeOnly}`);
  }

  getAgent(agentId) {
    return this._request("GET", `/agents/${agentId}`);
  }

  verify(agentId, publicKey, credentialHash = null) {
    return this._request("POST", `/agents/${agentId}/verify`, {
      public_key: publicKey,
      credential_hash: credentialHash
    });
  }

  getReputation(agentId) {
    return this._request("GET", `/agents/${agentId}/reputation`);
  }

  getHistory(agentId) {
    return this._request("GET", `/agents/${agentId}/history`);
  }

  stats() {
    return this._request("GET", "/dashboard/stats");
  }

updateReputation(agentId, interactionSuccess, violation = false, piiIncident = false, detail = null) {
    return this._request("POST", `/agents/${agentId}/reputation/update`, {
      interaction_success: interactionSuccess,
      violation,
      pii_incident: piiIncident,
      detail
    });
  }

  getReputationHistory(agentId) {
    return this._request("GET", `/agents/${agentId}/reputation/history`);
  }  

  trustLookup(agentId, publicKey, queryingAgent = null, minReputation = 0.7) {
    return this._request("POST", "/trust/lookup", {
      agent_id: agentId,
      public_key: publicKey,
      querying_agent: queryingAgent,
      min_reputation: minReputation
    });
  }

  listTrustLookups(limit = 50) {
    return this._request("GET", `/trust/lookups?limit=${limit}`);
  }
}

module.exports = AgentID;