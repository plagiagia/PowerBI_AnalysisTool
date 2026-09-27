"""Read-only inventory of a PBIP project's TMDL and PBIR artifacts."""

import json
import re
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON: {path}") from exc


def _table_inventory(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    columns = []
    measures = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("column "):
            columns.append(_identifier(stripped.removeprefix("column ")))
        elif stripped.startswith("measure "):
            measures.append(_identifier(stripped.removeprefix("measure ")))
    return {"name": path.stem, "columns": columns, "measures": measures}


def _identifier(value: str) -> str:
    match = re.match(r"'((?:[^']|'')*)'|([^\s=]+)", value)
    if not match:
        raise ValueError("Unsupported TMDL identifier")
    return (match.group(1) if match.group(1) is not None else match.group(2)).replace("''", "'")


def project_paths(project_root: str | Path):
    target = Path(project_root).resolve()
    candidates = [target] if target.is_file() else list(target.glob("*.pbip"))
    if len(candidates) != 1:
        raise ValueError("Specify one .pbip file or a folder containing exactly one project")
    pbip = candidates[0]
    reports = [a["report"]["path"] for a in _read_json(pbip)["artifacts"] if "report" in a]
    if len(reports) != 1:
        raise ValueError("This scanner currently requires exactly one report artifact")
    report = (pbip.parent / reports[0]).resolve()
    reference = _read_json(report / "definition.pbir")["datasetReference"]
    if "byPath" not in reference:
        raise ValueError("A local byPath semantic model is required")
    model = (report / reference["byPath"]["path"]).resolve()
    if not (model / "definition" / "tables").is_dir():
        raise ValueError("Local TMDL tables folder is missing")
    return pbip, report, model


def _fields(value):
    result = []
    if isinstance(value, dict):
        for kind in ("Column", "Measure"):
            field = value.get(kind)
            if isinstance(field, dict):
                entity = field.get("Expression", {}).get("SourceRef", {}).get("Entity")
                if entity:
                    item = {"table": entity, "name": field.get("Property"), "kind": kind}
                    if item not in result:
                        result.append(item)
        for child in value.values():
            for item in _fields(child):
                if item not in result:
                    result.append(item)
    elif isinstance(value, list):
        for child in value:
            for item in _fields(child):
                if item not in result:
                    result.append(item)
    return result


def scan_project(project_root: str | Path) -> dict[str, Any]:
    pbip, report, model_root = project_paths(project_root)
    root = pbip.parent
    report_root = report / "definition"
    tables_root = model_root / "definition" / "tables"

    tables = [_table_inventory(path) for path in sorted(tables_root.glob("*.tmdl"))]
    relationships = (model_root / "definition" / "relationships.tmdl").read_text(
        encoding="utf-8-sig", errors="replace"
    ) if (model_root / "definition" / "relationships.tmdl").exists() else ""

    pages = []
    pages_root = report_root / "pages"
    for page_json in sorted(pages_root.glob("*/page.json")):
        page = _read_json(page_json)
        visuals = []
        for visual_path in sorted((page_json.parent / "visuals").glob("*/visual.json")):
            visual = _read_json(visual_path)
            visuals.append({"id": visual_path.parent.name,
                            "type": visual.get("visual", {}).get("visualType", "group"),
                            "position": visual.get("position", {}), "fields": _fields(visual)})
        pages.append({
            "id": page_json.parent.name,
            "display_name": page.get("displayName") or page.get("name"),
            "visual_count": len(visuals),
            "width": page.get("width"), "height": page.get("height"),
            "visuals": visuals,
        })

    return {
        "project": root.name,
        "format": "PBIP",
        "semantic_model": {
            "tables": tables,
            "table_count": len(tables),
            "relationship_file_present": bool(relationships),
            "relationships": [dict(re.findall(r"^\s*(fromColumn|toColumn|crossFilteringBehavior):\s*(.+)$", block, re.M))
                              for block in re.split(r"(?m)^relationship ", relationships)[1:]],
        },
        "report": {
            "page_count": len(pages),
            "pages": pages,
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inventory a PBIP project")
    parser.add_argument("project", nargs="?", default=".")
    args = parser.parse_args()
    print(json.dumps(scan_project(args.project), indent=2))
