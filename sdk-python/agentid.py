import httpx
from typing import Optional


class AgentID:
    def __init__(self, base_url: str = "https://agent-id.onrender.com"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def health(self):
        r = self.client.get("/health")
        r.raise_for_status()
        return r.json()

    def register(self, agent_name: str, public_key: str, description: Optional[str] = None):
        """Register an agent and receive a cryptographic credential."""
        r = self.client.post("/agents", json={
            "agent_name": agent_name,
            "public_key": public_key,
            "description": description
        })
        r.raise_for_status()
        return r.json()

    def list_agents(self, active_only: bool = True):
        r = self.client.get("/agents", params={"active_only": str(active_only).lower()})
        r.raise_for_status()
        return r.json()

    def get_agent(self, agent_id: str):
        r = self.client.get(f"/agents/{agent_id}")
        r.raise_for_status()
        return r.json()

    def verify(self, agent_id: str, public_key: str, credential_hash: Optional[str] = None):
        """Verify an agent's cryptographic credential."""
        r = self.client.post(f"/agents/{agent_id}/verify", json={
            "public_key": public_key,
            "credential_hash": credential_hash
        })
        r.raise_for_status()
        return r.json()

    def get_reputation(self, agent_id: str):
        r = self.client.get(f"/agents/{agent_id}/reputation")
        r.raise_for_status()
        return r.json()

    def get_history(self, agent_id: str):
        r = self.client.get(f"/agents/{agent_id}/history")
        r.raise_for_status()
        return r.json()

    def stats(self):
        r = self.client.get("/dashboard/stats")
        r.raise_for_status()
        return r.json()

    def update_reputation(self, agent_id: str, interaction_success: bool,
                          violation: bool = False, pii_incident: bool = False,
                          detail: Optional[str] = None):
        r = self.client.post(f"/agents/{agent_id}/reputation/update", json={
            "interaction_success": interaction_success,
            "violation": violation,
            "pii_incident": pii_incident,
            "detail": detail
        })
        r.raise_for_status()
        return r.json()

    def get_reputation_history(self, agent_id: str):
        r = self.client.get(f"/agents/{agent_id}/reputation/history")
        r.raise_for_status()
        return r.json()    

    def trust_lookup(self, agent_id: str, public_key: str,
                     querying_agent: Optional[str] = None,
                     min_reputation: float = 0.7):
        r = self.client.post("/trust/lookup", json={
            "agent_id": agent_id,
            "public_key": public_key,
            "querying_agent": querying_agent,
            "min_reputation": min_reputation
        })
        r.raise_for_status()
        return r.json()

    def list_trust_lookups(self, limit: int = 50):
        r = self.client.get("/trust/lookups", params={"limit": limit})
        r.raise_for_status()
        return r.json()    
    
    def bridge_chainthread(self, chain_id: str, sender_id: str,
                           sender_public_key: str, receiver_id: Optional[str] = None,
                           min_reputation: float = 0.7):
        r = self.client.post("/bridge/chainthread", json={
            "chain_id": chain_id,
            "sender_id": sender_id,
            "sender_public_key": sender_public_key,
            "receiver_id": receiver_id,
            "min_reputation": min_reputation
        })
        r.raise_for_status()
        return r.json()

    def bridge_status(self):
        r = self.client.get("/bridge/status")
        r.raise_for_status()
        return r.json() 

    def revoke(self, agent_id: str, reason: Optional[str] = None):
        r = self.client.post(f"/agents/{agent_id}/revoke", json={"reason": reason})
        r.raise_for_status()
        return r.json()

    def reactivate(self, agent_id: str, public_key: str, reason: Optional[str] = None):
        r = self.client.post(f"/agents/{agent_id}/reactivate", json={
            "public_key": public_key,
            "reason": reason
        })
        r.raise_for_status()
        return r.json()   