"""
KSP Insight AI — Zoho Catalyst QuickML client
Location: assistant/ai/quickml_client.py

Required in .env:
    CATALYST_ORG_ID=...
    ZOHO_CLIENT_ID=...
    ZOHO_CLIENT_SECRET=...
    ZOHO_QUICKML_SCOPE=...

    QUICKML_SEVERITY_ENDPOINT_URL=...
    QUICKML_SEVERITY_ENDPOINT_KEY=...
    QUICKML_SOLVABILITY_ENDPOINT_URL=...
    QUICKML_SOLVABILITY_ENDPOINT_KEY=...
    QUICKML_PRIORITY_ENDPOINT_URL=...
    QUICKML_PRIORITY_ENDPOINT_KEY=...
    QUICKML_HOTSPOT_ENDPOINT_URL=...
    QUICKML_HOTSPOT_ENDPOINT_KEY=...
"""

import os
import time
import requests

_token_cache = {"access_token": None, "expires_at": 0}

MODEL_ENV_PREFIXES = {
    "severity": "QUICKML_SEVERITY",
    "solvability": "QUICKML_SOLVABILITY",
    "priority": "QUICKML_PRIORITY",
    "hotspot": "QUICKML_HOTSPOT",
}


def _get_access_token() -> str:
    """Returns a cached access token, requesting a fresh one if expired (~1hr lifetime)."""
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    client_id = os.getenv("ZOHO_CLIENT_ID")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET")
    scope = os.getenv("ZOHO_QUICKML_SCOPE", "QuickML.deployment.READ")
    org_id = os.getenv("CATALYST_ORG_ID")
    if not all([client_id, client_secret]):
        raise RuntimeError(
            "Missing ZOHO_CLIENT_ID / ZOHO_CLIENT_SECRET in .env — "
            "complete the Self Client setup at api-console.zoho.in before calling QuickML."
        )

    response = requests.post(
        "https://accounts.zoho.in/oauth/v2/token",
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": scope,
            "soid": f"ZohoCatalyst.{org_id}",
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600)
    return _token_cache["access_token"]


def predict(model_key: str, features: dict) -> dict:
    """
    model_key: one of "severity", "solvability", "priority", "hotspot"
    features: dict of column_name -> value, matching the columns the
              model was trained on.

    Returns the raw response dict from Catalyst, e.g.
        {"result": ["High"], "likelihood_score": [0.51], "explanation": {...}, "status": "success"}
    """
    if model_key not in MODEL_ENV_PREFIXES:
        raise ValueError(f"Unknown model_key '{model_key}', expected one of {list(MODEL_ENV_PREFIXES)}")

    prefix = MODEL_ENV_PREFIXES[model_key]
    endpoint_url = os.getenv(f"{prefix}_ENDPOINT_URL")
    endpoint_key = os.getenv(f"{prefix}_ENDPOINT_KEY")
    org_id = os.getenv("CATALYST_ORG_ID")

    if not all([endpoint_url, endpoint_key, org_id]):
        raise RuntimeError(
            f"Missing endpoint config for '{model_key}' model — check "
            f"{prefix}_ENDPOINT_URL / {prefix}_ENDPOINT_KEY / CATALYST_ORG_ID in .env."
        )

    access_token = _get_access_token()
    response = requests.post(
        endpoint_url,
        json={"data": features},
        headers={
            "X-QUICKML-ENDPOINT-KEY": endpoint_key,
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "CATALYST-ORG": org_id,
            # Confirmed via isolated testing: "Development" + explainModel=true
            # intermittently 500s. Production handles the same request reliably.
            "Environment": "Production",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()