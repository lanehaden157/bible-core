"""Keep the Claude.ai project's copy of the book's chat-side files current.

    python -m biblecore sync-check                  # which files changed since last pasted
    python -m biblecore sync-check --mark-synced [FILE ...]
    python -m biblecore sync                        # mirror into project-side/synced/,
                                                    # commit and push if anything changed

The file list is book.json "sync" (files + globs). The mirror is flat and
deliberately duplicated so a GitHub-connector "sync" source sees plain files.
Seeded from Joshua's check_project_sync.py + sync_to_github.py.
"""
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from biblecore.book import book


def _git(*args, check=True):
    return subprocess.run(["git", *args], cwd=book().root, capture_output=True,
                          text=True, check=check)


def hash_file(path):
    if not path.exists():
        return None
    return _git("hash-object", str(path)).stdout.strip()


def load_state():
    p = Path(book().path("sync_state"))
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_state(state):
    p = Path(book().path("sync_state"))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_main(argv=None):
    args = list(argv or [])
    root = Path(book().root)
    tracked = book().sync_files()
    state = load_state()

    if args and args[0] == "--mark-synced":
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for rel in args[1:] or tracked:
            if rel not in tracked:
                print(f"  skip (not tracked): {rel}")
                continue
            h = hash_file(root / rel)
            if h is None:
                print(f"  skip (missing on disk): {rel}")
                continue
            state[rel] = {"hash": h, "synced_at": now}
            print(f"  marked synced: {rel}")
        save_state(state)
        return 0

    stale, missing, ok = [], [], []
    for rel in tracked:
        current = hash_file(root / rel)
        if current is None:
            missing.append(rel)
        elif state.get(rel, {}).get("hash") != current:
            stale.append(rel)
        else:
            ok.append(rel)
    if stale:
        print("NEEDS RE-PASTE into the Claude.ai project:")
        for rel in stale:
            print(f"  - {rel}")
    if missing:
        print("MISSING on disk (referenced but not found):")
        for rel in missing:
            print(f"  - {rel}")
    if ok and not stale:
        print("Everything tracked is in sync.")
    elif ok:
        print(f"\n({len(ok)} file(s) already in sync)")
    if not tracked:
        print("book.json lists no sync files.")
    return 1 if stale else 0


def push_main(argv=None):
    root = Path(book().root)
    synced = Path(book().path("synced"))
    synced.mkdir(parents=True, exist_ok=True)
    missing = []
    for rel in book().sync_files():
        src = root / rel
        if not src.exists():
            missing.append(rel)
            continue
        shutil.copyfile(src, synced / Path(rel).name)
    for rel in missing:
        print(f"MISSING on disk (skipped): {rel}")

    status = _git("status", "--porcelain", "--", str(synced))
    if not status.stdout.strip():
        print("No changes to sync -- already up to date.")
        return 0
    changed = [line[3:] for line in status.stdout.splitlines()]
    _git("add", "--", str(synced))
    _git("commit", "-m", "Sync project-side docs\n\n" + "\n".join(f"- {c}" for c in changed))
    _git("push")
    print("Synced and pushed:")
    for c in changed:
        print(f"  - {c}")
    return 0
