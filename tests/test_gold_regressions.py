import json
import sys

import pytest

from new_game_plus_planner.cli import main
from new_game_plus_planner.core import evaluate, load_plan


def sample():
    return {
        "version": 1,
        "game": "Example",
        "items": [{"id": "goal", "title": "Prepare", "status": "pending", "required": True}],
    }


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("id", "  ", "blank"),
        ("title", "", "blank"),
        ("required", "false", "boolean"),
        ("required", 1, "boolean"),
        ("status", [], "invalid status"),
        ("category", {}, "invalid status"),
        ("depends_on", [1], "strings"),
        ("depends_on", [""], "strings"),
        ("depends_on", ["start", "start"], "duplicate dependencies"),
    ],
)
def test_strict_item_validation(tmp_path, field, value, message):
    data = sample()
    data["items"][0][field] = value
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises((ValueError, TypeError), match=message):
        load_plan(path)
    assert main([str(path)]) == 2


@pytest.mark.parametrize("version", [True, 1.0])
def test_version_must_be_integer(tmp_path, version):
    data = sample()
    data["version"] = version
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert main([str(path)]) == 2


def test_deep_acyclic_plan_validates_without_recursion(tmp_path):
    data = sample()
    data["items"] = [
        {
            "id": str(i),
            "title": str(i),
            "status": "done",
            "depends_on": [str(i + 1)] if i < 1499 else [],
        }
        for i in range(1500)
    ]
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate(load_plan(path))["ready"]
    data["items"][-1]["depends_on"] = ["0"]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="cycle"):
        load_plan(path)


def test_excessive_chain_report_has_bounded_error(tmp_path, capsys):
    data = sample()
    data["items"] = [
        {
            "id": str(i),
            "title": str(i),
            "status": "pending",
            "depends_on": [str(i + 1)] if i < 249 else [],
        }
        for i in range(250)
    ]
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert main([str(path)]) == 2
    assert "one million chain references" in capsys.readouterr().err


def test_default_required_and_existing_false_are_optional(tmp_path):
    data = sample()
    data["items"][0]["required"] = False
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate(load_plan(path))["ready"]
    del data["items"][0]["required"]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert evaluate(load_plan(path))["ready"]


def test_new_output_and_dangling_link(tmp_path):
    source = tmp_path / "plan.json"
    source.write_text(json.dumps(sample()), encoding="utf-8")
    output = tmp_path / "report.json"
    assert main([str(source), "--format", "json", "--output", str(output)]) == 0
    assert not json.loads(output.read_text())["ready"]
    target = tmp_path / "absent.md"
    link = tmp_path / "report.md"
    try:
        link.symlink_to(target)
    except OSError as exc:
        if sys.platform == "win32" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows account lacks symbolic-link privilege (1314)")
        raise
    assert main([str(source), "--output", str(link)]) == 2
    assert link.is_symlink() and not target.exists()


def test_exclusive_output_preserves_a_file_arriving_before_write(tmp_path, monkeypatch):
    from pathlib import Path

    source = tmp_path / "plan.json"
    source.write_text(json.dumps(sample()), encoding="utf-8")
    output = tmp_path / "report.md"
    original_open = Path.open

    def arriving_file(path, mode="r", *args, **kwargs):
        if path == output and mode == "x":
            with original_open(path, "w", encoding="utf-8") as stream:
                stream.write("keep")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", arriving_file)
    assert main([str(source), "--output", str(output)]) == 2
    assert output.read_text() == "keep"
