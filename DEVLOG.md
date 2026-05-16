# Devlog

This file records meaningful project changes so bugs, design decisions, and model behavior changes can be traced later.

## Rules

- Add a new entry for every code, data, model, or documentation change.
- Keep entries newest first.
- Mention changed files, user-visible behavior, verification steps, and any known risks.
- When a bug is fixed, include the symptom and the likely cause.
- When `game_data.json` or `game_model.pkl` changes, describe how the data/model was produced.

## Entry Template

```md
## YYYY-MM-DD - Short title

- Changed: files or systems touched.
- Why: reason for the change.
- Behavior: what should be different for players or developers.
- Verification: commands/tests/manual checks run.
- Risks/Notes: known limitations, follow-ups, or rollback clues.
```

## 2026-05-16 - Add project devlog

- Changed: added `DEVLOG.md`; documented the devlog workflow in `README.md`.
- Why: future changes need a searchable history for debugging gameplay, training, and model behavior.
- Behavior: no gameplay behavior changed.
- Verification: documentation-only change; reviewed project files and current structure.
- Risks/Notes: future functional changes should add their own entry above this one.
