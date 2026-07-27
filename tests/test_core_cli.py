import json

import pytest

from new_game_plus_planner.cli import main
from new_game_plus_planner.core import evaluate, load_plan, render_markdown


def plan():
    return {
        "version": 1,
        "game": "North Road",
        "items": [
            {
                "id": "quest",
                "title": "Finish companion quest",
                "category": "quests",
                "status": "pending",
                "required": True,
            },
            {
                "id": "gear",
                "title": "Upgrade carried gear",
                "category": "inventory",
                "status": "pending",
                "depends_on": ["quest"],
            },
            {
                "id": "choice",
                "title": "Record ending choice",
                "category": "decisions",
                "status": "done",
            },
        ],
    }


def test_evaluate_blocking_and_readiness():
    report = evaluate(plan())
    assert not report["ready"]
    assert report["items"][0]["state"] == "actionable"
    assert report["items"][1]["state"] == "blocked"
    assert "waiting for quest" in render_markdown(report)
    complete = plan()
    complete["items"][0]["status"] = "done"
    assert evaluate(complete)["ready"]


def test_validation_and_cycles(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan()), encoding="utf-8")
    assert load_plan(path)["game"] == "North Road"
    cycle = plan()
    cycle["items"][0]["depends_on"] = ["gear"]
    path.write_text(json.dumps(cycle), encoding="utf-8")
    with pytest.raises(ValueError, match="cycle"):
        load_plan(path)
    invalid = plan()
    invalid["items"][1]["depends_on"] = ["missing"]
    path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid dependency"):
        load_plan(path)


def test_cli_json_and_safe_output(tmp_path, capsys):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan()), encoding="utf-8")
    assert main([str(path), "--format", "json"]) == 0
    assert not json.loads(capsys.readouterr().out)["ready"]
    output = tmp_path / "report.md"
    output.write_text("keep", encoding="utf-8")
    assert main([str(path), "--output", str(output)]) == 2


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data.update(version=2), "version 1"),
        (lambda data: data.update(game=""), "game name"),
        (lambda data: data.update(items="bad"), "items must"),
        (lambda data: data["items"].append(data["items"][0].copy()), "duplicate item"),
        (lambda data: data["items"][0].update(status="unknown"), "invalid status"),
        (lambda data: data["items"][0].update(depends_on="quest"), "depends_on must"),
        (lambda data: data["items"][0].pop("title"), "requires string id and title"),
    ],
)
def test_input_validation(tmp_path, change, message):
    data = plan()
    change(data)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises((TypeError, ValueError), match=message):
        load_plan(path)
