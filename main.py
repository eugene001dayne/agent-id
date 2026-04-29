from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import json
import hashlib
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ISSUER = "AgentID Registry v0.1.0"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

app = FastAPI(
    title="AgentID",
    description="Cryptographic identity and reputation for AI agents.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def db():
    return httpx.Client(base_url=f"{SUPABASE_URL}/rest/v1", headers=HEADERS)


# --- Models ---

class AgentRegister(BaseModel):
    agent_name: str
    public_key: str
    description: Optional[str] = None

class VerifyRequest(BaseModel):
    public_key: str
    credential_hash: Optional[str] = None


# --- Helpers ---

def generate_credential_hash(agent_id: str, public_key: str, issuer: str) -> str:
    data = json.dumps({
        "agent_id": agent_id,
        "issuer": issuer,
        "public_key": public_key
    }, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()

def get_reputation_grade(score: float) -> str:
    if score >= 0.9: return "A"
    if score >= 0.75: return "B"
    if score >= 0.6: return "C"
    if score >= 0.4: return "D"
    return "F"

def log_history(client: httpx.Client, agent_id: str, event_type: str, detail: str):
    try:
        client.post("/credential_history", json={
            "agent_id": agent_id,
            "event_type": event_type,
            "detail": detail
        })
    except Exception:
        pass


# --- Routes ---

@app.get("/")
def root():
    return {
        "tool": "AgentID",
        "version": "0.1.0",
        "status": "running",
        "description": "Cryptographic identity and reputation for AI agents.",
        "suite": "Thread Suite"
    }

@app.get("/health")
def health():
    try:
        with db() as client:
            client.get("/agents", params={"limit": "1"})
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": "error", "detail": str(e)}


@app.post("/agents")
def register_agent(body: AgentRegister):
    """Register a new AI agent and issue a cryptographic credential."""
    agent_id = f"agent-{uuid.uuid4()}"
    created_at = datetime.now(timezone.utc).isoformat()
    credential_hash = generate_credential_hash(agent_id, body.public_key, ISSUER)

    with db() as client:
        existing = client.get("/agents", params={
            "public_key": f"eq.{body.public_key}",
            "select": "agent_id"
        })
        if existing.json():
            raise HTTPException(
                status_code=409,
                detail="A credential with this public key already exists."
            )

        r = client.post("/agents", json={
            "agent_id": agent_id,
            "agent_name": body.agent_name,
            "description": body.description,
            "public_key": body.public_key,
            "issuer": ISSUER,
            "credential_hash": credential_hash,
            "active": True
        })
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=f"Registration failed: {r.text}")

        client.post("/reputation", json={
            "agent_id": agent_id,
            "total_interactions": 0,
            "successful_interactions": 0,
            "violation_count": 0,
            "pii_incidents": 0,
            "reputation_score": 1.0
        })

        log_history(client, agent_id, "REGISTERED",
                    f"Agent '{body.agent_name}' registered. Issuer: {ISSUER}")

    return {
        "agent_id": agent_id,
        "agent_name": body.agent_name,
        "public_key": body.public_key,
        "issuer": ISSUER,
        "credential_hash": credential_hash,
        "active": True,
        "reputation_score": 1.0,
        "grade": "A",
        "created_at": created_at,
        "message": "Credential issued. Store your credential_hash — it proves your identity."
    }


@app.get("/agents")
def list_agents(active_only: bool = True):
    """List all registered agents."""
    with db() as client:
        params = {"order": "created_at.desc"}
        if active_only:
            params["active"] = "eq.true"
        r = client.get("/agents", params=params)
        agents = r.json()
        return {"agents": agents, "count": len(agents), "active_only": active_only}


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """Get an agent's full credential and reputation."""
    with db() as client:
        r = client.get("/agents", params={"agent_id": f"eq.{agent_id}"})
        if not r.json():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
        agent = r.json()[0]

        rep_r = client.get("/reputation", params={"agent_id": f"eq.{agent_id}"})
        reputation = rep_r.json()[0] if rep_r.json() else None

        if reputation:
            reputation["grade"] = get_reputation_grade(reputation["reputation_score"])

        return {"agent": agent, "reputation": reputation}


@app.post("/agents/{agent_id}/verify")
def verify_credential(agent_id: str, body: VerifyRequest):
    """Verify an agent's cryptographic credential."""
    with db() as client:
        r = client.get("/agents", params={"agent_id": f"eq.{agent_id}"})
        if not r.json():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
        agent = r.json()[0]

        if not agent["active"]:
            log_history(client, agent_id, "VERIFICATION_FAILED",
                        "Verification attempted on inactive credential.")
            return {
                "agent_id": agent_id,
                "verified": False,
                "reason": "Credential is inactive or has been revoked."
            }

        if agent["public_key"] != body.public_key:
            log_history(client, agent_id, "VERIFICATION_FAILED",
                        "Public key mismatch on verification attempt.")
            return {
                "agent_id": agent_id,
                "verified": False,
                "reason": "Public key does not match the registered credential."
            }

        recomputed = generate_credential_hash(
            agent_id,
            agent["public_key"],
            agent["issuer"]
        )
        hash_valid = recomputed == agent["credential_hash"]
        verified = hash_valid

        caller_hash_matched = None
        if body.credential_hash is not None:
            caller_hash_matched = body.credential_hash == agent["credential_hash"]

        rep_r = client.get("/reputation", params={"agent_id": f"eq.{agent_id}"})
        rep = rep_r.json()[0] if rep_r.json() else None

        log_history(client, agent_id,
                    "VERIFICATION_PASSED" if verified else "VERIFICATION_FAILED",
                    f"Verification {'succeeded' if verified else 'failed'}.")

    return {
        "agent_id": agent_id,
        "agent_name": agent["agent_name"],
        "verified": verified,
        "credential_hash_valid": hash_valid,
        "caller_hash_matched": caller_hash_matched,
        "issuer": agent["issuer"],
        "active": agent["active"],
        "reputation_score": rep["reputation_score"] if rep else None,
        "grade": get_reputation_grade(rep["reputation_score"]) if rep else None,
        "reason": "Credential verified successfully." if verified else "Credential hash mismatch — integrity check failed."
    }


@app.get("/agents/{agent_id}/reputation")
def get_reputation(agent_id: str):
    """Get an agent's full reputation record."""
    with db() as client:
        r = client.get("/agents", params={
            "agent_id": f"eq.{agent_id}",
            "select": "agent_id,agent_name,active"
        })
        if not r.json():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
        agent = r.json()[0]

        rep_r = client.get("/reputation", params={"agent_id": f"eq.{agent_id}"})
        if not rep_r.json():
            raise HTTPException(status_code=404, detail="Reputation record not found.")
        rep = rep_r.json()[0]

        score = rep["reputation_score"]
        return {
            "agent_id": agent_id,
            "agent_name": agent["agent_name"],
            "active": agent["active"],
            "reputation_score": score,
            "grade": get_reputation_grade(score),
            "total_interactions": rep["total_interactions"],
            "successful_interactions": rep["successful_interactions"],
            "violation_count": rep["violation_count"],
            "pii_incidents": rep["pii_incidents"],
            "last_updated": rep["last_updated"]
        }


@app.get("/agents/{agent_id}/history")
def get_history(agent_id: str):
    """Get the full credential event history for an agent."""
    with db() as client:
        r = client.get("/agents", params={"agent_id": f"eq.{agent_id}", "select": "agent_id"})
        if not r.json():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

        hist_r = client.get("/credential_history", params={
            "agent_id": f"eq.{agent_id}",
            "order": "created_at.desc"
        })
        return {
            "agent_id": agent_id,
            "history": hist_r.json(),
            "count": len(hist_r.json())
        }


@app.get("/dashboard/stats")
def dashboard_stats():
    """Overview stats for the dashboard."""
    with db() as client:
        agents_r = client.get("/agents", params={"select": "active"})
        agents = agents_r.json()
        total = len(agents)
        active = sum(1 for a in agents if a["active"])
        revoked = total - active

        rep_r = client.get("/reputation", params={"select": "reputation_score"})
        scores = [r["reputation_score"] for r in rep_r.json()]
        avg_score = round(sum(scores) / len(scores), 4) if scores else 0.0

        lookups_r = client.get("/trust_lookups", params={"select": "id"})
        total_lookups = len(lookups_r.json())

        hist_r = client.get("/credential_history", params={"select": "id"})
        total_events = len(hist_r.json())

        return {
            "total_agents": total,
            "active_agents": active,
            "revoked_agents": revoked,
            "avg_reputation_score": avg_score,
            "total_trust_lookups": total_lookups,
            "total_credential_events": total_events
        }