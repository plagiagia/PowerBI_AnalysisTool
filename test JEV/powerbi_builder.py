"""Inspect, validate and route a local Power BI build brief. No report writes."""
import argparse
import json
import time
from pathlib import Path

from powerbi_inventory import scan_project, project_paths, _read_json
from jev_client import power_bi_routing_decision


def validate(project, inventory):
    _, report, _ = project_paths(project)
    errors, warnings = [], []
    for path in (report / "definition").rglob("*.json"):
        try:
            _read_json(path)
        except ValueError:
            errors.append(f"Invalid JSON: {path.relative_to(report)}")
    tables = {t["name"]: t for t in inventory["semantic_model"]["tables"]}
    for table in tables.values():
        for key in ("columns", "measures"):
            if len(table[key]) != len(set(table[key])):
                errors.append(f"Duplicate {key} in {table['name']}")
    pages = inventory["report"]["pages"]
    metadata = _read_json(report / "definition/pages/pages.json")
    ids = {p["id"] for p in pages}
    order = metadata.get("pageOrder", [])
    if set(order) != ids or len(order) != len(ids):
        errors.append("Page order must reference every page exactly once")
    if metadata.get("activePageName") not in ids:
        errors.append("Active page does not exist")
    for page in pages:
        for visual in page["visuals"]:
            for field in visual["fields"]:
                table = tables.get(field["table"])
                key = "measures" if field["kind"] == "Measure" else "columns"
                if table is None or field["name"] not in table[key]:
                    errors.append(f"{page['display_name']}/{visual['id']}: unresolved {field}")
            pos = visual["position"]
            if all(k in pos for k in ("x", "y", "width", "height")) and page["width"] and page["height"]:
                if (pos["x"] < 0 or pos["y"] < 0 or
                    pos["x"] + pos["width"] > page["width"] + 1 or
                    pos["y"] + pos["height"] > page["height"] + 1):
                    warnings.append(f"Visual outside canvas: {page['display_name']}/{visual['id']}")
    return {"status": "failed" if errors else "passed_static_subset", "errors": errors,
            "warnings": warnings, "limits": ["No DAX execution or TMDL compiler validation",
            "No JSON Schema validation; JSON syntax and selected references only",
            "Field resolution covers direct Entity references, not query aliases or implicit date hierarchies",
            "Power BI Desktop rendering and metric reconciliation still required"]}


def make_plan(brief, inventory, checks, routing=None):
    next_step = "investigate_static_errors" if checks["errors"] else "codex_prepare_proposed_changes"
    advisory = "offline"
    if routing:
        answers = routing.get("answers", {})
        worker = answers.get("worker", {})
        action = answers.get("action", {})
        if worker.get("choice") not in {"MODEL_AGENT", "DAX_AGENT", "REPORT_AGENT", "VALIDATION_AGENT"}:
            raise ValueError("Invalid Jev worker response")
        if action.get("choice") not in {"inspect", "generate", "validate", "review", "finish"}:
            raise ValueError("Invalid Jev action response")
        confidence = min(worker.get("confidence", 0), action.get("confidence", 0))
        advisory = "use_routing_hint" if confidence >= .9 else "codex_resolve_ambiguity"
    return {"brief": brief, "status": "planned", "next_step": next_step,
            "routing_policy": advisory, "routing": routing,
            "tasks": [
                {"id": "inspect", "status": "complete", "worker": "SCANNER"},
                {"id": "design", "depends_on": ["inspect"], "worker": "REPORT_AGENT",
                 "instruction": "Read existing visual definitions and measure expressions; map the brief to existing fields and specify exact pages, visuals and bindings."},
                {"id": "generate", "depends_on": ["design"], "worker": "CODEX",
                 "instruction": "For an authoring brief, generate only requested changes in a separate PBIP copy. For inspection/planning briefs, deliver the proposal and skip generation. Reuse existing visual schemas and semantic definitions. Parallelize only disjoint files."},
                {"id": "validate", "depends_on": ["generate"], "worker": "VALIDATION_AGENT",
                 "instruction": "Run static checks on the copy; compare new findings against baseline; then verify in Desktop when available."}],
            "inventory": inventory, "validation": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inspect", "validate", "plan"])
    parser.add_argument("--project", default=".")
    parser.add_argument("--brief")
    parser.add_argument("--jev", action="store_true", help="Send metadata and brief to Jev for advisory routing")
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        inventory = scan_project(args.project)
        if args.command == "inspect":
            result = inventory
        else:
            checks = validate(args.project, inventory)
            if args.command == "validate":
                result = checks
            else:
                if not args.brief:
                    parser.error("plan requires --brief")
                routing = power_bi_routing_decision(inventory, args.brief) if args.jev else None
                result = make_plan(args.brief, inventory, checks, routing)
        result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        print(json.dumps(result, indent=2))
        return 1 if result.get("errors") else 0
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
