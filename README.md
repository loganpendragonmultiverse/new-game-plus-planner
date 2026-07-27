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
