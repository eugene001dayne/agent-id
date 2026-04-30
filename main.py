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

THREAD_SUITE_URLS = {
    "iron-thread": "https://iron-thread.onrender.com",
    "testthread": "https://test-thread-cass.onrender.com",
    "promptthread": "https://prompt-thread.onrender.com",
    "chainthread": "https://chain-thread.onrender.com",
    "policythread": "https://policy-thread.onrender.com",
    "threadwatch": "https://thread-watch.onrender.com",
    "behavioral-fingerprint": "https://behavioral-fingerprint.onrender.com"
}

app = FastAPI(
    title="AgentID",
    description="Cryptographic identity and reputation for AI agents.",
    version="0.4.0"
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

class ReputationUpdate(BaseModel):
    interaction_success: bool
    violation: bool = False
    pii_incident: bool = False
    detail: Optional[str] = None

class TrustLookupRequest(BaseModel):
    agent_id: str
    public_key: str
    querying_agent: Optional[str] = None
    min_reputation: float = 0.7

class ChainThreadBridgeRequest(BaseModel):
    chain_id: str
    sender_id: str
    sender_public_key: str
    receiver_id: Optional[str] = None
    min_reputation: float = 0.7


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

def compute_reputation_score(
    total: int,
    successful: int,
    violations: int,
    pii_incidents: int
) -> float:
    if total == 0:
        return 1.0
    base = successful / total
    violation_penalty = violations * 0.02
    pii_penalty = pii_incidents * 0.05
    return round(max(0.0, min(1.0, base - violation_penalty - pii_penalty)), 4)

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
        "version": "0.4.0",
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


@app.post("/agents/{agent_id}/reputation/update")
def update_reputation(agent_id: str, body: ReputationUpdate):
    """Submit an interaction outcome and update the agent's reputation score."""
    with db() as client:
        r = client.get("/agents", params={
            "agent_id": f"eq.{agent_id}",
            "select": "agent_id,agent_name,active"
        })
        if not r.json():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
        if not r.json()[0]["active"]:
            raise HTTPException(status_code=400,
                                detail="Cannot update reputation for inactive agent.")

        rep_r = client.get("/reputation", params={"agent_id": f"eq.{agent_id}"})
        if not rep_r.json():
            raise HTTPException(status_code=404, detail="Reputation record not found.")
        rep = rep_r.json()[0]

        score_before = rep["reputation_score"]
        new_total = rep["total_interactions"] + 1
        new_successful = rep["successful_interactions"] + (1 if body.interaction_success else 0)
        new_violations = rep["violation_count"] + (1 if body.violation else 0)
        new_pii = rep["pii_incidents"] + (1 if body.pii_incident else 0)

        score_after = compute_reputation_score(
            new_total, new_successful, new_violations, new_pii
        )

        client.patch(
            f"/reputation?agent_id=eq.{agent_id}",
            json={
                "total_interactions": new_total,
                "successful_interactions": new_successful,
                "violation_count": new_violations,
                "pii_incidents": new_pii,
                "reputation_score": score_after,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        )

        client.post("/reputation_history", json={
            "agent_id": agent_id,
            "score_before": score_before,
            "score_after": score_after,
            "interaction_success": body.interaction_success,
            "violation": body.violation,
            "pii_incident": body.pii_incident,
            "detail": body.detail
        })

        log_history(client, agent_id, "REPUTATION_UPDATED",
                    f"Score {score_before} → {score_after}. "
                    f"Success: {body.interaction_success}, "
                    f"Violation: {body.violation}, PII: {body.pii_incident}")

    return {
        "agent_id": agent_id,
        "score_before": score_before,
        "score_after": score_after,
        "grade_before": get_reputation_grade(score_before),
        "grade_after": get_reputation_grade(score_after),
        "total_interactions": new_total,
        "successful_interactions": new_successful,
        "violation_count": new_violations,
        "pii_incidents": new_pii,
        "interaction_success": body.interaction_success,
        "violation": body.violation,
        "pii_incident": body.pii_incident
    }


@app.get("/agents/{agent_id}/reputation/history")
def get_reputation_history(agent_id: str):
    """Get the full reputation score history for an agent."""
    with db() as client:
        r = client.get("/agents", params={"agent_id": f"eq.{agent_id}",
                                          "select": "agent_id"})
        if not r.json():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")

        hist_r = client.get("/reputation_history", params={
            "agent_id": f"eq.{agent_id}",
            "order": "created_at.desc"
        })
        history = hist_r.json()

        rep_r = client.get("/reputation", params={"agent_id": f"eq.{agent_id}"})
        rep = rep_r.json()[0] if rep_r.json() else None

        return {
            "agent_id": agent_id,
            "current_score": rep["reputation_score"] if rep else None,
            "current_grade": get_reputation_grade(rep["reputation_score"]) if rep else None,
            "total_events": len(history),
            "history": history
        }


@app.get("/agents/{agent_id}/history")
def get_history(agent_id: str):
    """Get the full credential event history for an agent."""
    with db() as client:
        r = client.get("/agents", params={"agent_id": f"eq.{agent_id}",
                                          "select": "agent_id"})
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


@app.post("/trust/lookup")
def trust_lookup(body: TrustLookupRequest):
    """
    One-call trust decision for any agent.
    Verifies credential, checks reputation, returns trusted: true/false.
    """
    with db() as client:
        r = client.get("/agents", params={"agent_id": f"eq.{body.agent_id}"})
        if not r.json():
            result = {
                "agent_id": body.agent_id,
                "trusted": False,
                "reason": "Agent not found in registry.",
                "credential_valid": False,
                "reputation_score": None,
                "grade": None,
                "querying_agent": body.querying_agent,
                "min_reputation": body.min_reputation
            }
            client.post("/trust_lookups", json={
                "querying_agent": body.querying_agent,
                "queried_agent": body.agent_id,
                "result": result
            })
            return result

        agent = r.json()[0]

        if not agent["active"]:
            result = {
                "agent_id": body.agent_id,
                "agent_name": agent["agent_name"],
                "trusted": False,
                "reason": "Agent credential is inactive or revoked.",
                "credential_valid": False,
                "reputation_score": None,
                "grade": None,
                "querying_agent": body.querying_agent,
                "min_reputation": body.min_reputation
            }
            client.post("/trust_lookups", json={
                "querying_agent": body.querying_agent,
                "queried_agent": body.agent_id,
                "result": result
            })
            return result

        if agent["public_key"] != body.public_key:
            result = {
                "agent_id": body.agent_id,
                "agent_name": agent["agent_name"],
                "trusted": False,
                "reason": "Public key does not match registered credential.",
                "credential_valid": False,
                "reputation_score": None,
                "grade": None,
                "querying_agent": body.querying_agent,
                "min_reputation": body.min_reputation
            }
            client.post("/trust_lookups", json={
                "querying_agent": body.querying_agent,
                "queried_agent": body.agent_id,
                "result": result
            })
            return result

        recomputed = generate_credential_hash(
            body.agent_id,
            agent["public_key"],
            agent["issuer"]
        )
        credential_valid = recomputed == agent["credential_hash"]

        if not credential_valid:
            result = {
                "agent_id": body.agent_id,
                "agent_name": agent["agent_name"],
                "trusted": False,
                "reason": "Credential hash integrity check failed.",
                "credential_valid": False,
                "reputation_score": None,
                "grade": None,
                "querying_agent": body.querying_agent,
                "min_reputation": body.min_reputation
            }
            client.post("/trust_lookups", json={
                "querying_agent": body.querying_agent,
                "queried_agent": body.agent_id,
                "result": result
            })
            return result

        rep_r = client.get("/reputation", params={"agent_id": f"eq.{body.agent_id}"})
        rep = rep_r.json()[0] if rep_r.json() else None
        score = rep["reputation_score"] if rep else 1.0
        grade = get_reputation_grade(score)
        meets_threshold = score >= body.min_reputation
        trusted = credential_valid and meets_threshold

        reason = "Agent is trusted. Credential valid and reputation meets threshold."
        if not meets_threshold:
            reason = (f"Reputation score {score} is below the required "
                      f"minimum of {body.min_reputation}.")

        result = {
            "agent_id": body.agent_id,
            "agent_name": agent["agent_name"],
            "trusted": trusted,
            "reason": reason,
            "credential_valid": credential_valid,
            "reputation_score": score,
            "grade": grade,
            "total_interactions": rep["total_interactions"] if rep else 0,
            "violation_count": rep["violation_count"] if rep else 0,
            "querying_agent": body.querying_agent,
            "min_reputation": body.min_reputation,
            "issuer": agent["issuer"],
            "looked_up_at": datetime.now(timezone.utc).isoformat()
        }

        client.post("/trust_lookups", json={
            "querying_agent": body.querying_agent,
            "queried_agent": body.agent_id,
            "result": result
        })

        log_history(client, body.agent_id, "TRUST_LOOKUP",
                    f"Queried by '{body.querying_agent}'. "
                    f"Trusted: {trusted}. Score: {score}.")

    return result


@app.get("/trust/lookups")
def list_trust_lookups(limit: int = 50):
    """List all trust lookup records."""
    with db() as client:
        r = client.get("/trust_lookups", params={
            "order": "created_at.desc",
            "limit": str(limit)
        })
        lookups = r.json()
        return {"lookups": lookups, "count": len(lookups)}


@app.post("/bridge/chainthread")
def bridge_chainthread(body: ChainThreadBridgeRequest):
    """
    ChainThread bridge — verify a sender agent's identity and reputation
    before a handoff envelope is accepted.
    ChainThread calls this endpoint when processing an envelope.
    """
    with db() as client:
        r = client.get("/agents", params={"agent_id": f"eq.{body.sender_id}"})

        if not r.json():
            result = {
                "chain_id": body.chain_id,
                "sender_id": body.sender_id,
                "receiver_id": body.receiver_id,
                "identity_verified": False,
                "trusted": False,
                "reason": "Sender agent not found in AgentID registry.",
                "reputation_score": None,
                "grade": None,
                "recommendation": "BLOCK — sender has no registered identity."
            }
            log_history(client, body.sender_id, "CHAINTHREAD_BRIDGE",
                        f"Chain {body.chain_id}: sender not found in registry.")
            return result

        agent = r.json()[0]

        if not agent["active"]:
            result = {
                "chain_id": body.chain_id,
                "sender_id": body.sender_id,
                "receiver_id": body.receiver_id,
                "identity_verified": False,
                "trusted": False,
                "reason": "Sender agent credential is inactive or revoked.",
                "reputation_score": None,
                "grade": None,
                "recommendation": "BLOCK — sender credential revoked."
            }
            log_history(client, body.sender_id, "CHAINTHREAD_BRIDGE",
                        f"Chain {body.chain_id}: sender credential inactive.")
            return result

        if agent["public_key"] != body.sender_public_key:
            result = {
                "chain_id": body.chain_id,
                "sender_id": body.sender_id,
                "receiver_id": body.receiver_id,
                "identity_verified": False,
                "trusted": False,
                "reason": "Sender public key does not match registered credential.",
                "reputation_score": None,
                "grade": None,
                "recommendation": "BLOCK — identity mismatch."
            }
            log_history(client, body.sender_id, "CHAINTHREAD_BRIDGE",
                        f"Chain {body.chain_id}: public key mismatch.")
            return result

        recomputed = generate_credential_hash(
            body.sender_id,
            agent["public_key"],
            agent["issuer"]
        )
        identity_verified = recomputed == agent["credential_hash"]

        rep_r = client.get("/reputation", params={"agent_id": f"eq.{body.sender_id}"})
        rep = rep_r.json()[0] if rep_r.json() else None
        score = rep["reputation_score"] if rep else 1.0
        grade = get_reputation_grade(score)
        meets_threshold = score >= body.min_reputation
        trusted = identity_verified and meets_threshold

        if not identity_verified:
            recommendation = "BLOCK — credential integrity check failed."
        elif not meets_threshold:
            recommendation = (f"BLOCK — reputation {score} below required {body.min_reputation}.")
        else:
            recommendation = "ALLOW — identity verified and reputation meets threshold."

        result = {
            "chain_id": body.chain_id,
            "sender_id": body.sender_id,
            "sender_name": agent["agent_name"],
            "receiver_id": body.receiver_id,
            "identity_verified": identity_verified,
            "trusted": trusted,
            "reason": recommendation,
            "credential_valid": identity_verified,
            "reputation_score": score,
            "grade": grade,
            "total_interactions": rep["total_interactions"] if rep else 0,
            "violation_count": rep["violation_count"] if rep else 0,
            "min_reputation": body.min_reputation,
            "recommendation": recommendation,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

        client.post("/trust_lookups", json={
            "querying_agent": body.receiver_id,
            "queried_agent": body.sender_id,
            "result": result
        })

        log_history(client, body.sender_id, "CHAINTHREAD_BRIDGE",
                    f"Chain {body.chain_id}: trusted={trusted}, score={score}.")

    return result


@app.get("/bridge/status")
def bridge_status():
    """Poll all Thread Suite tools and return online/offline status."""
    results = {}
    for tool, url in THREAD_SUITE_URLS.items():
        try:
            r = httpx.get(f"{url}/health", timeout=5.0)
            results[tool] = {
                "status": "online" if r.status_code == 200 else "degraded",
                "url": url
            }
        except Exception:
            results[tool] = {"status": "offline", "url": url}
    return {
        "agentid": {"status": "online", "url": "https://agent-id.onrender.com"},
        **results,
        "checked_at": datetime.now(timezone.utc).isoformat()
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