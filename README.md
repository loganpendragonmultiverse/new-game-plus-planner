# New Game Plus Planner

[![CI](https://github.com/loganpendragonmultiverse/new-game-plus-planner/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/new-game-plus-planner/actions/workflows/ci.yml)

New Game Plus Planner organizes cleanup, inventory, quests, decisions, and other preparation before another playthrough. It distinguishes completed, actionable, blocked, and skipped items and calculates readiness from explicitly required tasks.

## Three-minute start

```bash
python -m pip install .
ngplus-plan examples/plan.json
ngplus-plan examples/plan.json --format json
```

Item dependencies are validated for missing references, self-dependencies, and cycles. Blocking is derived from dependency completion, while optional and required items remain visibly distinct.

The tool does not read game saves, know what carries into New Game Plus, or provide game-specific advice. The user supplies and maintains the checklist. A ready report only means every locally marked required item is done. Requires Python 3.10 or newer.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).

## Blocker chains and next prerequisites

Reports now include `blocker_chains` per pending item. Each path starts with that item and follows unmet dependencies in sorted ID order, preserving both paths through a diamond. Completed prerequisites end a path; skipped prerequisites remain blockers and are never listed as actionable.

The top-level `prerequisite_frontier` lists sorted actionable IDs that can move incomplete required goals forward, including an actionable required goal itself. Optional goals do not create extra work, but an optional prerequisite of a required goal can appear in the frontier. An empty frontier can mean skipped blockers need reconsideration; it does not imply readiness. Readiness continues to require every explicitly required item to be done. The planner only reads the supplied plan and never accesses saves or games.
