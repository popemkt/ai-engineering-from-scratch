# HARNESS.md — local agent index

Entry point for AI agents (e.g. Claude Code) working in **this local clone**. Indexes the
docs, states the environment constraints, and defines how the tutor agent runs lessons.
Read before running code or debugging "command not found" / wrong-version issues.

The repo is a **fork** (origin = `github.com/popemkt/ai-engineering-from-scratch`,
upstream = `github.com/rohitg00/ai-engineering-from-scratch`). The setup files below are
**committed to the fork** (portable across machines); pull curriculum updates with
`git fetch upstream && git rebase upstream/main`.

Context: macOS (Apple M4), Determinate Nix + home-manager, direnv + nix-direnv.

## Complete setup — every file

| File | In git? | Purpose |
|------|---------|---------|
| `.nix/flake.nix` | committed | Toolchain devShell: python312, uv, nodejs_22, pnpm, git. |
| `.nix/flake.lock` | committed | Pins nixpkgs. |
| `.envrc` | committed | direnv: `use flake "path:$PWD/.nix"` + `.venv/bin` on PATH. |
| `.venv/` | gitignored | uv-managed python libs (numpy, torch). Built per-machine. |
| `.direnv/` | gitignored | nix-direnv cache. Built per-machine. |
| [LEARNING.md](LEARNING.md) | committed | Study loop + auto-rendered progress table. |
| `learn/progress.py` | committed | Progress tracker CLI (stdlib). |
| `learn/progress.json` | committed | Completed-lessons data (source of truth). |
| HARNESS.md | committed | This index. |
| `AGENTS.md` | committed | Links here (curriculum file; rebase may touch it). |

`.venv/` + `.direnv/` are in `.gitignore` (machine-specific, rebuilt). Claude's persistent
**memory** lives at `~/.claude/projects/<repo>/memory/` — that's the memory system, not env
setup, and does not travel with the fork.

To reproduce on a new machine: clone fork → `cd` in (direnv builds toolchain) →
`direnv exec . uv pip install --python "$PWD/.venv/bin/python" numpy torch`.

## Teaching protocol (for the tutor agent)

The user is a seasoned dev — skip git/lang/tooling basics; lead with the non-obvious.

- **Quizzes via the Ask tool.** When a lesson has `quiz.json`, present its questions using
  the `AskUserQuestion` tool (one call, batch the questions), not as plain prose. Map each
  quiz option to an answer choice; after the user answers, confirm correct/incorrect with
  the lesson's `explanation`. This applies to any curriculum-provided questions.
  **Shuffle the options — never always put the correct answer first.**
- Keep the per-lesson loop from [LEARNING.md](LEARNING.md), but compress the parts the user
  already knows. Lead with intuition + the one thing that's easy to get wrong.
- **Track progress** with `learn/progress.py`: at lesson end run
  `direnv exec . python3 learn/progress.py done <phase> <lesson> [--quiz X/Y] [--note ...]`
  (auto-renders the table into LEARNING.md). `… next` shows what's up next.

---

## TL;DR for running code

```bash
direnv exec . python3 path/to/main.py      # run project python (3.12, from .venv/flake)
direnv exec . node path/to/main.js         # node 22 from flake
direnv exec . uv pip install --python "$PWD/.venv/bin/python" <pkg>   # add a python lib
```

Always prefix project commands with `direnv exec .`. Plain `python3`/`node` resolve to
system/homebrew versions (wrong).

---

## Why the prefix is required (the harness facts)

1. **The Bash tool shell is non-interactive.** It sources only `~/.zshenv` (a nix-store
   read-only symlink). It does **not** read `~/.zshrc`/`~/.zprofile`/`~/.zlogin`, so the
   interactive `direnv` shell hook never fires. Verified: `login=no interactive=no`.

2. **The harness controls PATH and overrides both injection points:**
   - PATH set/modified in a profile (`.zshenv`) is **discarded** — the command runs in a
     separate shell with the harness's own PATH (non-PATH env vars *do* survive).
   - A `PATH` key in `.claude/settings*.json` `env` is **ignored**. (`${PATH}` is also not
     expanded there.) Non-PATH env vars in `env` (e.g. `ZDOTDIR`) *are* applied.
   - Net: you cannot make project tools win PATH automatically. Use `direnv exec`, which is
     direnv's official non-interactive entrypoint.

3. **cwd persists between Bash calls; env vars do not.** Each call is a fresh shell. Also,
   `cd` into a subdir may be reset to the repo root by the harness — prefer absolute paths.

4. The user's **own terminal** has the direnv hook in `~/.zshrc` and auto-activates the
   env normally. These constraints apply to the agent's Bash tool only.

---

## Project env layout

- **Toolchain:** Nix flake at `~/.claude/envs/ai-eng-from-scratch/flake.nix` (kept *outside*
  this repo so the curriculum git stays clean; a path-flake outside any git repo needs no
  `git add`). Provides `python312`, `uv`, `nodejs_22`, `pnpm`, `git`.
- **`.envrc`** (repo root): `use flake <that path>` + `PATH_add .venv/bin`. `direnv allow`ed,
  cached by nix-direnv.
- **Python libs:** installed by `uv` into `./.venv` (NOT from nix — nixpkgs torch on darwin
  is fragile). `uv pip install` must target `--python "$PWD/.venv/bin/python"`; plain
  `uv pip install` hits the read-only nix python and is refused.
- **Verified working:** python 3.12.13, torch 2.12.0 (MPS available + GPU matmul ok),
  numpy 2.4.6.

## Git hygiene

These local-only paths are in `.git/info/exclude` (never committed):
`.envrc`, `.direnv/`, `.venv/`, `LEARNING.md`, `HARNESS.md`.
