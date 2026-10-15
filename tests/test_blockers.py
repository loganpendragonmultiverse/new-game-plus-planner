from new_game_plus_planner.core import evaluate, render_markdown


def item(id, dependencies=(), status="pending", required=False):
    return {
        "id": id,
        "title": id,
        "status": status,
        "required": required,
        "depends_on": list(dependencies),
    }


def test_diamond_frontier_and_chains_are_deterministic():
    data = {
        "game": "Test",
        "items": [
            item("goal", ["right", "left"], required=True),
            item("left", ["start"]),
            item("right", ["start"]),
            item("start"),
        ],
    }
    result = evaluate(data)
    assert result["prerequisite_frontier"] == ["start"]
    assert result["items"][0]["blocker_chains"] == [
        ["goal", "left"],
        ["goal", "left", "start"],
        ["goal", "right"],
        ["goal", "right", "start"],
    ]
    assert "goal -> left -> start" in render_markdown(result)
    assert result == evaluate(data)


def test_skipped_stays_blocking_and_has_no_actionable_frontier():
    result = evaluate(
        {
            "game": "Test",
            "items": [item("goal", ["skip"], required=True), item("skip", status="skipped")],
        }
    )
    assert result["prerequisite_frontier"] == []
    assert result["items"][0]["state"] == "blocked"
    assert result["items"][0]["blocker_chains"] == [["goal", "skip"]]
    assert not result["ready"]


def test_completed_dependencies_cut_chains_and_optional_goals_do_not_expand_frontier():
    result = evaluate(
        {
            "game": "Test",
            "items": [
                item("goal", ["done"], required=True),
                item("done", ["old"], status="done"),
                item("old"),
                item("optional", ["old"]),
            ],
        }
    )
    assert result["prerequisite_frontier"] == ["goal"]
    assert result["items"][0]["blocker_chains"] == []
    result["items"][0]["status"] = "done"
    assert evaluate({"game": "Test", "items": result["items"]})["ready"]


def test_only_completed_required_items_means_empty_frontier():
    report = evaluate({"game": "Test", "items": [item("done", status="done", required=True)]})
    assert report["ready"] and report["prerequisite_frontier"] == []
