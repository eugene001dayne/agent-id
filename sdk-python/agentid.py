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