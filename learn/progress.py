#!/usr/bin/env python3
"""Personal progress tracker for working through the curriculum.

Source of truth: learn/progress.json (completed lessons) + the filesystem
(the full ordered lesson list is derived from phases/**/docs/en.md, so we never
hardcode the 503 lessons). Also renders a table into LEARNING.md.

Usage:
    progress.py next                       # first not-done lesson
    progress.py done 0 2 --quiz 3/3        # mark phase 0 / lesson 2 done
    progress.py undo 0 2                    # unmark
    progress.py stats                       # totals + per-phase
    progress.py list [--phase 0]           # show statuses
    progress.py render                      # rewrite the table in LEARNING.md

Stdlib only. Run via: direnv exec . python3 learn/progress.py <cmd>
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASES = ROOT / "phases"
DATA = Path(__file__).resolve().parent / "progress.json"
LEARNING = ROOT / "LEARNING.md"
START, END = "<!-- progress:start -->", "<!-- progress:end -->"

NN = re.compile(r"^(\d\d)-(.+)$")


def lessons() -> list[dict]:
    """Ordered list of every lesson from the filesystem."""
    out = []
    for ph in sorted(p for p in PHASES.iterdir() if p.is_dir() and NN.match(p.name)):
        pn, pslug = NN.match(ph.name).groups()
        for ls in sorted(l for l in ph.iterdir() if l.is_dir() and NN.match(l.name)):
            if not (ls / "docs" / "en.md").exists():
                continue
            ln, lslug = NN.match(ls.name).groups()
            out.append({"key": f"{pn}/{ln}", "phase": pn, "lesson": ln,
                        "phase_slug": pslug, "slug": lslug, "path": ls.relative_to(ROOT)})
    return out


def load() -> dict:
    if DATA.exists():
        return json.loads(DATA.read_text())
    return {"completed": {}}


def save(d: dict) -> None:
    DATA.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")


def key(phase: str, lesson: str) -> str:
    return f"{int(phase):02d}/{int(lesson):02d}"


def cmd_next(_a) -> None:
    done = load()["completed"]
    for ls in lessons():
        if ls["key"] not in done:
            print(f"NEXT  {ls['key']}  {ls['slug']}")
            print(f"      docs: {ls['path']}/docs/en.md")
            return
    print("All lessons complete. 🎉")


def cmd_done(a) -> None:
    d = load()
    k = key(a.phase, a.lesson)
    valid = {l["key"]: l for l in lessons()}
    if k not in valid:
        raise SystemExit(f"no such lesson: {k}")
    d["completed"][k] = {"slug": valid[k]["slug"], "quiz": a.quiz,
                         "note": a.note, "ts": date.today().isoformat()}
    save(d)
    render()
    print(f"done  {k}  {valid[k]['slug']}" + (f"  quiz {a.quiz}" if a.quiz else ""))


def cmd_undo(a) -> None:
    d = load()
    k = key(a.phase, a.lesson)
    if d["completed"].pop(k, None):
        save(d); render(); print(f"undone  {k}")
    else:
        print(f"{k} was not marked done")


def cmd_stats(_a) -> None:
    done = load()["completed"]
    all_ls = lessons()
    by_phase: dict[str, list[int]] = {}
    for ls in all_ls:
        d, t = by_phase.setdefault(ls["phase"], [0, 0])[0], by_phase[ls["phase"]]
        t[1] += 1
        if ls["key"] in done:
            t[0] += 1
    tot_done = sum(1 for ls in all_ls if ls["key"] in done)
    print(f"TOTAL  {tot_done}/{len(all_ls)} lessons  ({100*tot_done//len(all_ls)}%)")
    for ph in sorted(by_phase):
        dn, tt = by_phase[ph]
        bar = "█" * (10 * dn // tt) + "·" * (10 - 10 * dn // tt)
        print(f"  P{ph}  [{bar}] {dn}/{tt}")


def cmd_list(a) -> None:
    done = load()["completed"]
    for ls in lessons():
        if a.phase is not None and int(ls["phase"]) != a.phase:
            continue
        mark = "✓" if ls["key"] in done else " "
        q = done.get(ls["key"], {}).get("quiz") or ""
        print(f"[{mark}] {ls['key']}  {ls['slug']:<40} {q}")


def table() -> str:
    done = load()["completed"]
    rows = ["| Phase | Lesson | Status | Quiz | Note |", "|---|---|---|---|---|"]
    nxt = next((l for l in lessons() if l["key"] not in done), None)
    for ls in lessons():
        info = done.get(ls["key"])
        if info:
            status, q, note = "✅ done", info.get("quiz") or "-", info.get("note") or ""
        elif nxt and ls["key"] == nxt["key"]:
            status, q, note = "▶ next", "", ""
        else:
            continue  # don't list the hundreds of not-yet-reached lessons
        rows.append(f"| {ls['phase']} | {ls['lesson']} {ls['slug']} | {status} | {q} | {note} |")
    return "\n".join(rows)


def render() -> None:
    if not LEARNING.exists():
        return
    txt = LEARNING.read_text()
    block = f"{START}\n{table()}\n{END}"
    if START in txt and END in txt:
        txt = re.sub(re.escape(START) + r".*?" + re.escape(END), block, txt, flags=re.S)
    else:
        txt = txt.rstrip() + "\n\n## Progress\n\n" + block + "\n"
    LEARNING.write_text(txt)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("next").set_defaults(fn=cmd_next)
    d = sub.add_parser("done"); d.add_argument("phase"); d.add_argument("lesson")
    d.add_argument("--quiz"); d.add_argument("--note"); d.set_defaults(fn=cmd_done)
    u = sub.add_parser("undo"); u.add_argument("phase"); u.add_argument("lesson"); u.set_defaults(fn=cmd_undo)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)
    li = sub.add_parser("list"); li.add_argument("--phase", type=int); li.set_defaults(fn=cmd_list)
    sub.add_parser("render").set_defaults(fn=lambda _a: render())
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
