# ui/api_client.py
"""
HTTP client for the BackTestii FastAPI backend.

Authenticates as an internal trusted client using the
X-Internal-Client-Key header. No user login required.

Environment variables:
    BACKEND_URL           Base URL           (default: http://127.0.0.1:8000)
    INTERNAL_CLIENT_KEY   Shared secret key  (required — must match backend)
"""

import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
INTERNAL_CLIENT_KEY = os.getenv("INTERNAL_CLIENT_KEY", "")


def _url(path: str) -> str:
    return f"{BACKEND_URL.rstrip('/')}{path}"


def _headers() -> dict:
    """Return auth headers for internal client requests."""
    return {"X-Internal-Client-Key": INTERNAL_CLIENT_KEY}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def health_check() -> dict:
    """GET /health — verify backend is reachable."""
    resp = requests.get(_url("/health"), timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_strategies() -> dict:
    """GET /strategies — return the full strategy registry."""
    resp = requests.get(_url("/strategies"), headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_instruments(exchange: str | None = None) -> list[str]:
    """GET /instruments — return sorted instrument names for an exchange."""
    params = {}
    if exchange:
        params["exchange"] = exchange
    resp = requests.get(_url("/instruments"), params=params, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


def resolve_symbol(name: str, exchange: str | None = None) -> str:
    """GET /instruments/resolve — resolve display name to Yahoo Finance ticker."""
    params = {"name": name}
    if exchange:
        params["exchange"] = exchange
    resp = requests.get(_url("/instruments/resolve"), params=params, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()["symbol"]


def run_backtest(
    ticker: str,
    strategy_key: str,
    strategy_params: dict | None,
    start_date,
    end_date,
    capital: float,
) -> dict:
    """
    POST /backtest — run a backtest via the FastAPI backend.

    Authenticates using the X-Internal-Client-Key header.
    Returns the full JSON response dict.
    """
    payload = {
        "ticker": ticker,
        "strategy_key": strategy_key,
        "strategy_params": strategy_params or {},
        "start_date": str(start_date),
        "end_date": str(end_date),
        "capital": float(capital),
    }

    resp = requests.post(
        _url("/backtest"),
        json=payload,
        headers=_headers(),
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()
