# Working on NodiNajar

Judges score teamwork from roles and commit history, so every member commits their own work under their own name.

## One-time setup

```bash
git config --global user.name  "Your Name"
git config --global user.email "the email on your GitHub account"
git clone https://github.com/<org-or-user>/nodinajar.git
cd nodinajar
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Every change

1. Pull first: `git pull`
2. Make a branch: `git checkout -b <your-name>/<what>` (for example `rafi/tighten-aoi`)
3. Run `pytest -q` before you commit. If you touched `src/compute`, add or update a test.
4. Commit with a message that says what changed: `git commit -m "Tighten Jamuna AOI to the channel belt"`
5. Push and open a pull request: `git push -u origin <branch>`. One other member reviews it.

## Rules

- Never commit `.env`, tokens, passwords or downloaded NASA files. `.gitignore` blocks the usual ones; check `git status` before you commit.
- Large data stays in `cache/`. Only the small files the demo needs go in `web/demo_fixtures/`, written by `build_demo.py`.
- Never remove the SYNTHETIC or PROVISIONAL labels.
- If an AI tool wrote code or text you kept, add a line to `docs/AI_USE.md` in the same commit.
- Ground-truth events: one row per event in `ground_truth/events.csv`, with a source link. Put your name in `verified_by` after you've read the source yourself. Run `python tools/check_events.py`.
