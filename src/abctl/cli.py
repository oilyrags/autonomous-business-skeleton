"""abctl — one discoverable entry point for the skeleton's demos and gates.

    uv run python -m abctl --help
    uv run python -m abctl demo          # the 60-second infra-free story
    uv run python -m abctl loop          # any single demo by name

Every command is infra-free (ports + stubs); `abctl demo` chains the story-ordered highlights.
This wraps the same module mains the Makefile targets call — no new behaviour, one front door.
"""

from __future__ import annotations

import argparse
import importlib
from collections.abc import Sequence

# name -> (module with a main() in its __main__, one-line description)
COMMANDS: dict[str, tuple[str, str]] = {
    "growth": ("ab_growth.__main__", "experiments decide scale/pivot/kill per business"),
    "ideate": ("ab_growth.ideate_demo", "ideation → scored → gated → governed experiment"),
    "product": ("ab_product.product_demo", "initiative → charter-conformant scaffold → gated SDLC → deploy"),
    "factory": ("ab_factory.__main__", "provision + readiness-gate new businesses"),
    "portfolio": ("ab_portfolio.__main__", "recycle capital from losers into winners"),
    "econ": ("ab_econ.__main__", "unit economics: profit/CAC/LTV/payback per business"),
    "loop": ("ab_portfolio.loop_demo", "ledger spend -> econ verdict -> portfolio allocation"),
    "revenue": ("ab_revenue.__main__", "customer charges booked to the ledger as income"),
    "ads": ("ab_ads.__main__", "paid acquisition with closed-loop attribution"),
    "mvp": ("ab_mvp.__main__", "Blueprint -> landing page -> deployed URL"),
    "sales": ("ab_sales.__main__", "qualify -> quote -> close; won deals become revenue"),
    "social": ("ab_social.__main__", "plan -> generate -> QA -> publish -> optimize content"),
    "obs": ("ab_obs.__main__", "fleet overview + cost attribution + anomalies"),
    "playbook": ("ab_playbook.__main__", "distil winners into a reusable blueprint"),
    "memory": ("ab_memory.__main__", "per-business memory with scoped recall"),
    "org": ("ab_org.__main__", "authority-based decision routing + escalation"),
    "sandbox": ("ab_sandbox.__main__", "tool capability policy + audit"),
    "monitor": ("ab_monitor.__main__", "deterministic checks as Nagios plugin results"),
    "console": ("ab_console.__main__", "render the control-plane Fleet Dashboard (smoke)"),
    "inboxiq": ("ab_examples.inboxiq", "the worked example: one B2B SaaS through every context"),
}

# The 60-second story: money loop, marketing loop, then watch + steer it.
DEMO_STORY: tuple[str, ...] = ("growth", "portfolio", "loop", "social", "monitor", "console")


def run(name: str) -> int:
    """Run one command's module main(); returns its exit code."""
    module_path, _ = COMMANDS[name]
    module = importlib.import_module(module_path)
    result = module.main()
    return int(result or 0)


def demo() -> int:
    """The infra-free story, in order — the fastest way to see the skeleton work end to end."""
    for i, name in enumerate(DEMO_STORY, 1):
        _, blurb = COMMANDS[name]
        print(f"\n=== [{i}/{len(DEMO_STORY)}] {name} — {blurb} ===")
        code = run(name)
        if code != 0:
            return code
    print("\ndemo complete — every step ran deterministically, no infrastructure required.")
    print("next: `make console-serve` for the live control plane, `make up` for the secure stack.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="abctl", description="Control the autonomous-business skeleton's demos and gates."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="run the 60-second infra-free story (the best first command)")
    for name, (_, blurb) in COMMANDS.items():
        sub.add_parser(name, help=blurb)
    args = parser.parse_args(argv)
    return demo() if args.command == "demo" else run(args.command)
