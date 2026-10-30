# TPC Plugin Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this approved plan. Steps use checkboxes for tracking.

**Goal:** One installable `tpc` plugin exposes six skills and includes the existing offline Python implementation.

**Architecture:** Keep the repository root as the plugin root and `skills/` as the sole skill source. Build a filtered, self-contained ZIP; prepare Python dependencies in a separate user-selected virtual environment. CST remains an external, lazy dependency.

**Tech Stack:** Python standard library, pytest, Codex plugin manifests and marketplace, existing tpc-topology package.

**Spec:** User-approved six-skill proposal in this chat, 2026-10-30.

## Global Constraints

- Preserve existing Python import names and the original three skill names.
- Include `lattice-paths`, `topological-schematic`, `topological-modeling`, `topological-templates`, `topological-analysis`, `topological-optimization`.
- Do not touch the old migration source or launch CST/EM solves.
- Ship only code, documentation, tests and clearly licensed resources; no caches, experiments or machine configuration.
- No hardcoded checkout paths. No bundled generic CST service/MCP implementation.
- User already approved implementation and local installation; no repeated design approval. Work in this clean checkout and leave changes reviewable without publishing or pushing.

## Review Focus

- Installed cache is outside the source checkout: relative references and imports must still work.
- Untracked caches and private work files must never enter the ZIP.
- Python environments may be missing dependencies; checking must not mutate, preparation must be explicit.
- Existing standalone skill copies must be identified and preserved before any conflict resolution.
- Plugin activation and offline checks must not be described as real CST validation.

### Task 1: Packaging and runtime

Files: `plugin.json`, `.codex-plugin/plugin.json`, `scripts/build_plugin.py`, `scripts/plugin_runtime.py`, `tests/test_plugin_distribution.py`.

Interfaces: `build_plugin(source: Path, output: Path) -> Path`; runtime CLI `--check` or `--prepare --venv PATH [--extras geometry,science,yaml]` returns JSON with Python and plugin root.

- [x] Write and run failing tests for a filtered ZIP, extraction outside the checkout, and side-effect-free runtime checks.
- [x] Implement manifests, allowlisted packaging and runtime dependency preparation.
- [x] Run tests and a real extracted-package import smoke check.

### Task 2: Six skills

Files: existing `skills/**`; three new skill folders; `docs/PLUGIN.md`.

- [x] Read baseline skill evaluation and record missing entry points and portable runtime guidance.
- [x] Add template, analysis and optimization reference skills, verifying each against real offline API examples.
- [x] Add shared runtime guidance and links to existing skills; retain geometry approval and evidence boundaries.
- [x] Validate all six frontmatters and links; independently exercise installed reference workflows.

### Task 3: Install and acceptance

Files: marketplace metadata, `.github/workflows/ci.yml`, `MANIFEST.in`, `README.md`, `docs/VALIDATION.md`.

- [x] Add repeatable build/validation documentation and CI packaging check.
- [x] Run full offline suite, Python distribution build and ZIP inventory checks.
- [x] Register/install using supported Codex plugin tooling; verify enabled identity and six cached skill entries.
- [x] Check existing standalone copies and report any restart/new-chat requirement accurately.
- [x] Record actual results, review diff and leave changes unpushed.

## Execution ledger

- Ruling: use the current clean checkout; user asked to implement this repository and install locally. No solver or remote publication is included.
- Task 1: complete; 7 packaging/runtime regressions passed, including an extracted-cache smoke check. Initial 5 tests failed before implementation; review regressions reproduced 2 failures before the fixes.
- Task 2: complete; six frontmatters validated, three new reference examples independently executed outside the plugin directory, and 53 local links checked. Existing geometry approval and frequency acceptance rules retained.
- Review: fixed nested cache inclusion and dependency probe false positives; shared runtime guidance now matches script output. Standalone copies match repository HEAD with no custom differences.
- Task 3: complete; 545 passed, 1 integration deselected; wheel/sdist and plugin ZIP built; native CLI installed and enabled tpc@tpc-local 0.1.0. Actual cache smoke passed in a new venv. Three standalone originals moved to a recoverable backup. No CST action or remote publish performed.
- Final acceptance: native skills/list from a directory outside the checkout returned all six tpc:<skill-name> entries enabled. Installed cache content matched every file in the final ZIP.
