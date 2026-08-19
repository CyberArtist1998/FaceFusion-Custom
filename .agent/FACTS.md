# FACTS: FaceFusion

**GENERATED FILE - do not edit by hand.** Regenerate with:

```
python repo_probe.py D:\MyWorld-Sync\011-AI\FaceFusion --deep
```

Every row below was produced by inspecting this machine. Rows marked
UNVERIFIED were inferred from config files but not executed - treat them
as claims, not facts.

## Interpreter

| Path | Version | Status |
|---|---|---|
| `venv_311/Scripts/python.exe` | 3.11.9 | VERIFIED |

**Use this interpreter:** `venv_311/Scripts/python.exe` (Python 3.11.9)

_System Python is `3.14.6` at `C:\Python314\python.exe`._
_It is NOT this project's interpreter. Do not install into it._

## Commands

| Role | Command | Status | Evidence |
|---|---|---|---|
| test | `venv_311/Scripts/python.exe -m pytest` | FAILED - tool not installed in this interpreter | tests/ directory |
| typecheck | `venv_311/Scripts/python.exe -m mypy .` | FAILED - tool not installed in this interpreter | mypy.ini |
| lint | `venv_311/Scripts/python.exe -m flake8` | FAILED - tool not installed in this interpreter | .flake8 |
| lint | `npm run lint` | FAILED - tool not installed in this interpreter | package.json scripts.lint -> eslint . |

## Closure oracle

**No verified command available.** Until one exists, an agent cannot
prove it is finished, and a human owns the closure decision.

## Package manager

`npm` (chosen by the lockfile present, not by habit)

## Rules that follow from the above

1. Use the interpreter path exactly as written. Do not substitute `python`.
2. Never install into the system interpreter.
3. Never `--force-reinstall` or `--upgrade` against a system-wide
   interpreter: it deletes files before rewriting them and breaks any
   process currently using them.
4. A source build usually means no wheel exists for this Python version,
   not that a compiler is missing.
5. If a row above says UNVERIFIED or FAILED, treat the command as unproven.
   Do not report success on the strength of it.

