# HARNESS.md — local agent index

Entry point for AI agents (e.g. Claude Code) working in **this local clone**. Indexes the
machine-specific docs and states the environment constraints. Not curriculum content; kept
out of git via `.git/info/exclude`. Read before running code or debugging "command not
found" / wrong-version issues.

Context: macOS (Apple M4), Determinate Nix + home-manager, direnv + nix-direnv.

## Complete setup — every file (all in-repo, git-excluded)

| File | Tracked? | Purpose |
|------|----------|---------|
| `.nix/flake.nix` | excluded | Toolchain devShell: python312, uv, nodejs_22, pnpm, git. |
| `.nix/flake.lock` | excluded | Pins nixpkgs. |
| `.envrc` | excluded | direnv: `use flake "path:$PWD/.nix"` + `.venv/bin` on PATH. |
| `.venv/` | excluded | uv-managed python libs (numpy, torch). Built by uv, not nix. |
| `.direnv/` | excluded | nix-direnv cache. |
| [LEARNING.md](LEARNING.md) | excluded | **Progress tracking** + per-lesson study loop. |
| HARNESS.md | excluded | This index. |
| `AGENTS.md` | tracked (curriculum) | Links here; marked `git update-index --skip-worktree` so the link never shows/commits. |

Exclusions live in `.git/info/exclude`. **Nothing in `~/.claude` is needed for the env** —
the flake is in-repo via a `path:` flakeref (reads filesystem, no git-tracking needed; only
`.nix/` is copied to the store, not the whole repo). The sole `~/.claude` thing is Claude's
own **memory** at `~/.claude/projects/<repo>/memory/` — that's the memory system, not env setup.

To reproduce from scratch: create `.nix/flake.nix` + `.envrc`, `direnv allow`, then
`direnv exec . uv pip install --python "$PWD/.venv/bin/python" numpy torch`.

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
