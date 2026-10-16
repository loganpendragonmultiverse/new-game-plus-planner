# Development

## 1.1.0 - 2026-10-15

Reports now include `blocker_chains` per pending item. Each path starts with that item and follows unmet dependencies in sorted ID order, preserving both paths through a diamond. Completed prerequisites end a path; skipped prerequisites remain blockers and are never listed as actionable.

The top-level `prerequisite_frontier` lists sorted actionable IDs that can move incomplete required goals forward, including an actionable required goal itself. Optional goals do not create extra work, but an optional prerequisite of a required goal can appear in the frontier. An empty frontier can mean skipped blockers need reconsideration; it does not imply readiness. Readiness continues to require every explicitly required item to be done. The planner only reads the supplied plan and never accesses saves or games.

Merge and release require independent review and the repository CI gates.
