"""Minimal server-side client for TypeSafe Jev System One."""

import json
import os
import sys
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from powerbi_inventory import scan_project


ENDPOINT = "https://api.typesafe.ai/v1/systemone"


def _load_local_env() -> None:
    """Load a minimal .env file without adding a dependency."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path) or os.environ.get("TYPESAFE_API_KEY"):
        return
    with open(env_path, encoding="utf-8-sig") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if name.strip() == "TYPESAFE_API_KEY" and value:
                os.environ["TYPESAFE_API_KEY"] = value


def ask(state: Any, questions: dict[str, dict[str, Any]], model: str = "jev-latest") -> dict[str, Any]:
    _load_local_env()
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        raise RuntimeError("Set TYPESAFE_API_KEY in the server environment before calling Jev.")

    payload = json.dumps({"model": model, "state": state, "questions": questions}).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Jev HTTP {exc.code}; check authentication, quota or request format.") from None
    except URLError as exc:
        raise RuntimeError(f"Could not reach Jev: {exc.reason}") from exc


def power_bi_routing_decision(project_inventory: dict[str, Any], request: str) -> dict[str, Any]:
    """Classify a Power BI build request before invoking specialist workers."""
    return ask(
        state={"request": request, "project": project_inventory},
        questions={
            "worker": {
                "type": "choice",
                "instructions": "Which specialist should handle the next Power BI task?",
                "criteria": {
                    "MODEL_AGENT": "Create or modify tables, columns, relationships, or model metadata.",
                    "DAX_AGENT": "Create or modify DAX measures or calculated logic.",
                    "REPORT_AGENT": "Create or modify pages, visuals, filters, or report layout.",
                    "VALIDATION_AGENT": "Inspect errors, broken references, invalid JSON/TMDL, or consistency.",
                },
            },
            "action": {
                "type": "choice",
                "instructions": "What should happen next in the Power BI build workflow?",
                "criteria": {
                    "inspect": "Read and understand the current project before editing.",
                    "generate": "Generate or modify a project artifact.",
                    "validate": "Run deterministic checks on generated artifacts.",
                    "review": "Ask for human review because the decision is ambiguous or risky.",
                    "finish": "The requested work is complete and verified.",
                },
            },
        },
    )


if __name__ == "__main__":
    inventory = scan_project(".")
    request = "Create an executive expenses dashboard"
    print(json.dumps(power_bi_routing_decision(inventory, request), indent=2))
