"""Re-derive everything downstream of the committed fragments. Safe to re-run.

    python -m biblecore build

Hard steps (the build fails if one does):
  assets              css/core.css, css/components.css, data/components.json,
                      components-reference.md for the enabled components
  retrofit            fragment edits from the retrofit specs (idempotent)
  refresh             regenerate each built fragment's meta block
  validate            every built fragment against the contract
  scan                -> data/occurrences.json
  verify-occurrences  independent recount + tagged-flag check
  roots               data/roots.json integrity
  digest              data/threads.json -> threads-digest.md
  canon               echo edges -> data/canon.json (canon.py)
  manifest            -> data/manifest.json (manifest.py)
Advisory (reported, never fail the build):
  audit               tracked-thread coverage in built units
  leads               canon-leads for built units + the next one
  sync-check          chat-side files changed since last synced

units/*.html are the source of truth; nothing here regenerates them from
source-artifacts/. A new unit is `python -m biblecore port N`.

A book that needs a different sequence writes its own build script that
calls these steps (ARCHITECTURE.md §5: override, don't edit).
"""
from biblecore import (assets, audit, canon, digest, leads, manifest, refresh,
                       retrofit, roots, scan, sync, validate_units, verify_occurrences)

STEPS = [
    ("assets", assets.main),
    ("retrofit", retrofit.main),
    ("refresh", refresh.main),
    ("validate", validate_units.main),
    ("scan", scan.main),
    ("verify-occurrences", verify_occurrences.main),
    ("roots", roots.main),
    ("digest", digest.main),
    ("canon", canon.main),
    ("manifest", manifest.main),
]
ADVISORY = [
    ("audit", lambda: audit.main(["--check"])),
    ("leads", lambda: leads.main([])),
    ("sync-check", lambda: sync.check_main([])),
]


def main(argv=None):
    for name, fn in STEPS:
        print(f"\n=== {name} ===")
        rc = fn([])
        if rc:
            print(f"\nFAILED at {name}")
            return rc
    for name, fn in ADVISORY:
        print(f"\n=== {name} (advisory) ===")
        try:
            fn()
        except Exception as exc:  # advisory: report, never fail
            print(f"  ({name} unavailable: {exc})")
    print("\nbuild ok")
    return 0
