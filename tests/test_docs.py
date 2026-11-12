"""The instruction files core owns stay inside their size budgets
(selftest.DOC_BUDGET_KB). A book's own files only warn (`biblecore test`,
check `docs`); these fail, because every book and every chat loads them.
To add a rule, cut one; raising a budget is Lane's call."""
import os

import support
from biblecore.selftest import DOC_BUDGET_KB

OWNED = {
    "card_research": "canon/card-research.md",
    "card_verse": "canon/card-verse.md",
    "card_build": "canon/card-build.md",
    "card_condensed": "canon/card-condensed.md",
    "lens": "template/lens.md",
    "contract": "canon/contract.md",
    "book_guide": "biblecore/BOOK_CLAUDE.md",
    "field": "template/CHAT_SIDE_INSTRUCTIONS.md",
    "claude": "template/CLAUDE.md",
    "style_reference": "template/{{SLUG}}_study_style_reference.md",
}
# core's own CLAUDE.md, read by every core session
CORE_CLAUDE_KB = 5.5


def _kb(rel):
    return os.path.getsize(os.path.join(support.CORE, rel)) / 1000


def test_core_owned_docs_are_within_budget():
    fails = []
    for key, rel in OWNED.items():
        kb = _kb(rel)
        if kb > DOC_BUDGET_KB[key]:
            fails.append(f"{rel} is {kb:.1f} KB, budget {DOC_BUDGET_KB[key]}: "
                         f"cut or move something (CLAUDE.md, 'Keeping them lean')")
    kb = _kb("CLAUDE.md")
    if kb > CORE_CLAUDE_KB:
        fails.append(f"CLAUDE.md is {kb:.1f} KB, budget {CORE_CLAUDE_KB}")
    return fails


def test_every_owned_doc_has_a_budget():
    return [f"{k}: no budget" for k in OWNED if k not in DOC_BUDGET_KB]


TESTS = [test_core_owned_docs_are_within_budget, test_every_owned_doc_has_a_budget]
