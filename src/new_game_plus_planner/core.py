from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

STATUSES = {"pending", "done", "skipped"}
CATEGORIES = {"cleanup", "inventory", "quests", "decisions", "other"}


def load_plan(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(data, dict)
        or type(data.get("version")) is not int
        or data.get("version") != 1
    ):
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
        if not item["id"].strip() or not item["title"].strip():
            raise ValueError("item id and title must not be blank")
        if not isinstance(item.get("required", False), bool):
            raise TypeError(f"item {item['id']} required must be a boolean")
        if item["id"] in by_id:
            raise ValueError(f"duplicate item id: {item['id']}")
        if (
            not isinstance(item.get("status"), str)
            or item.get("status") not in STATUSES
            or not isinstance(item.get("category", "other"), str)
            or item.get("category", "other") not in CATEGORIES
        ):
            raise ValueError(f"item {item['id']} has an invalid status or category")
        if not isinstance(item.get("depends_on", []), list):
            raise TypeError(f"item {item['id']} depends_on must be a list")
        dependencies = item.get("depends_on", [])
        if any(
            not isinstance(dependency, str) or not dependency.strip() for dependency in dependencies
        ):
            raise TypeError(f"item {item['id']} dependencies must be nonblank strings")
        if len(dependencies) != len(set(dependencies)):
            raise ValueError(f"item {item['id']} has duplicate dependencies")
        by_id[item["id"]] = item
    for item in items:
        for dependency in item.get("depends_on", []):
            if dependency not in by_id or dependency == item["id"]:
                raise ValueError(f"item {item['id']} has an invalid dependency")
    visiting: set[str] = set()
    visited: set[str] = set()
    for item_id in by_id:
        stack = [(item_id, False)]
        while stack:
            current, exiting = stack.pop()
            if exiting:
                visiting.remove(current)
                visited.add(current)
            elif current in visiting:
                raise ValueError("dependency cycle detected")
            elif current not in visited:
                visiting.add(current)
                stack.append((current, True))
                stack.extend(
                    (dependency, False)
                    for dependency in reversed(by_id[current].get("depends_on", []))
                )
    return data


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    by_id = {item["id"]: item for item in data["items"]}

    chain_references = 0

    def chains(item_id: str, prefix: list[str]) -> list[list[str]]:
        nonlocal chain_references
        result = []
        stack = [(item_id, prefix)]
        while stack:
            current, path = stack.pop()
            if current != item_id:
                chain_references += len(path)
                if chain_references > 1_000_000:
                    raise ValueError(
                        "dependency report exceeds one million chain references; split the plan"
                    )
                result.append(path)
            for dependency in sorted(set(by_id[current].get("depends_on", [])), reverse=True):
                if by_id[dependency]["status"] != "done":
                    stack.append((dependency, [*path, dependency]))
        return result

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
                "blocker_chains": chains(item["id"], [item["id"]])
                if item["status"] == "pending"
                else [],
            }
        )
    counts = Counter(item["state"] for item in evaluated)
    required_incomplete = [
        item for item in evaluated if item["required"] and item["status"] != "done"
    ]
    actionable = {item["id"] for item in evaluated if item["state"] == "actionable"}
    frontier = sorted(
        {
            chain[-1]
            for item in evaluated
            if item["required"] and item["status"] == "pending"
            for chain in [[item["id"]], *item["blocker_chains"]]
            if chain[-1] in actionable
        }
    )
    return {
        "prerequisite_frontier": frontier,
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
    lines.extend(
        [
            "Actionable prerequisite frontier: "
            + (", ".join(report["prerequisite_frontier"]) or "None"),
            "",
        ]
    )
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
            for chain in item["blocker_chains"]:
                lines.append("  - Blocker chain: " + " -> ".join(chain))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
