from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

STATUSES = {"pending", "done", "skipped"}
CATEGORIES = {"cleanup", "inventory", "quests", "decisions", "other"}


def load_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("plan must be a version 1 object")
    if not isinstance(data.get("game"), str) or not data["game"].strip():
        raise ValueError("plan requires a game name")
    items = data.get("items")
    if not isinstance(items, list):
        raise TypeError("items must be a list")
    by_id = {}
    for item in items:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not isinstance(item.get("title"), str)
        ):
            raise TypeError("each item requires string id and title")
        if item["id"] in by_id:
            raise ValueError(f"duplicate item id: {item['id']}")
        if item.get("status") not in STATUSES or item.get("category", "other") not in CATEGORIES:
            raise ValueError(f"item {item['id']} has an invalid status or category")
        if not isinstance(item.get("depends_on", []), list):
            raise TypeError(f"item {item['id']} depends_on must be a list")
        by_id[item["id"]] = item
    for item in items:
        for dependency in item.get("depends_on", []):
            if dependency not in by_id or dependency == item["id"]:
                raise ValueError(f"item {item['id']} has an invalid dependency")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visiting:
            raise ValueError("dependency cycle detected")
        if item_id in visited:
            return
        visiting.add(item_id)
        for dependency in by_id[item_id].get("depends_on", []):
            visit(dependency)
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in by_id:
        visit(item_id)
    return data


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    by_id = {item["id"]: item for item in data["items"]}
    evaluated = []
    for item in data["items"]:
        unmet = [
            dependency
            for dependency in item.get("depends_on", [])
            if by_id[dependency]["status"] != "done"
        ]
        state = item["status"]
        if state == "pending":
            state = "blocked" if unmet else "actionable"
        evaluated.append(
            {
                **item,
                "category": item.get("category", "other"),
                "required": item.get("required", False),
                "state": state,
                "unmet_dependencies": unmet,
            }
        )
    counts = Counter(item["state"] for item in evaluated)
    required_incomplete = [
        item for item in evaluated if item["required"] and item["status"] != "done"
    ]
    return {
        "version": 1,
        "game": data["game"],
        "ready": not required_incomplete,
        "required_incomplete": len(required_incomplete),
        "counts": dict(sorted(counts.items())),
        "items": evaluated,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['game']} New Game Plus Plan",
        "",
        f"Ready: **{'Yes' if report['ready'] else 'No'}** · Required items remaining: **{report['required_incomplete']}**",
        "",
    ]
    for category in sorted(CATEGORIES):
        items = [item for item in report["items"] if item["category"] == category]
        if not items:
            continue
        lines.extend([f"## {category.title()}", ""])
        for item in items:
            marker = "x" if item["status"] == "done" else " "
            required = " · required" if item["required"] else ""
            blocked = (
                f" · waiting for {', '.join(item['unmet_dependencies'])}"
                if item["unmet_dependencies"]
                else ""
            )
            lines.append(f"- [{marker}] **{item['title']}** — {item['state']}{required}{blocked}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
