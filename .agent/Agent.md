# Agent Commend

## Root Directory:
D:\MyWorld-Sync\011-AI\FaceFusion

## Init:
Read the file AGENTS.md in the repo root before starting. Follow its rules. If it does not exist, create an emepty one.

## Scope:
general framework for running a small local model (~30B class) against an unfamiliar codebase for any task: locate, modify, refactor, remove, extend.

## TASK:
Go through all the Steps then Ask User to state it's request

## RULES :
1. Core thesis: the binding constraint is not the model's intelligence. It is verifiability. Structure every task so that each step has a cheap mechanical oracle. Delegate where an oracle exists. Do not delegate where none does.
2. Every phase writes a file. Nothing important lives only in context. Context is a cache. Disk is memory.
3. This single rule fixes:
   1. state-block corruption (state lives in a file, not in a token stream)
   2. loop repetition (worklist file is checked and appended)
   3. crash resumability (restart reads the file)
   4. reviewability (you read the artifact, not a 200-turn transcript)
   5. context exhaustion (findings are summarized to disk, then dropped)
   6. Minimum artifact set per task:
4. I will guide you and be by your side for every decision you want to take if you are in doubt or something is unknown.
5. State the full path of the interpreter you are targeting before you act.
6. Never install into the Python you are running on But Use this project's venv explicitly: `./venv/Scripts/python.exe -m pip ...` or `uv pip install --python ./venv/Scripts/python.exe ...`.
7. Never use `--force-reinstall` or `--upgrade` against a system-wide interpreter — it deletes files before rewriting them and destroys any process currently using them.
8. Let the resolver choose versions on Python 3.14 rather than forcing pins. A source build usually means no wheel exists, not that a compiler is missing.


## DO NOT:
- Edit any other file.
- Remove or reword existing comments or code.

## REQUIRED FILES TO READ AND TO WORK WITH - Rise alert and stop the task completely if any of it is messing.
  .agent/
  REPO-MAP.md # written once per repo, committed
  worklist.txt # pending units, one per line
  done.txt # completed units
  findings.md # what was located, with file:line
  questions.md # escalations awaiting your answer
  decisions.md # your answers, appended

## REPORT:
  CHANGED: <file>
  COMMAND OUTPUT: <paste>
  EXIT CODE: <number>
  COMMIT: <hash or none>

# This project

FaceFusion 3.6.1, running from a **root-flattened layout**: app source sits at
the repo root (`facefusion.py`, `facefusion/` package), with a Python 3.14 venv
at `venv/`.

Launch it with:

```
./venv/Scripts/python.exe facefusion.py run
```
## Verify before you claim

Check facts in the current environment before reporting them. If a module looks
missing, import it. If you quote a log, confirm its paths belong to this machine
and this checkout.

## Debugging

Check the `logs/` folder before changing anything — `logs/api/` for launcher
scripts, `logs/shell/` for direct runs. Prefer the `latest` file for a current
issue and timestamped files for history, but confirm provenance first.
