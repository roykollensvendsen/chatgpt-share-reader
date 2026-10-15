"""Command line for chatgpt-share-reader."""

from __future__ import annotations

import argparse
import sys

from chatgpt_share_reader import share

#: Every verb this command has. The documentation test requires each one to
#: appear in a worked example, so a verb cannot be added without one.
COMMANDS: tuple[str, ...] = ("read",)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch. Returns a process exit code."""
    parser = argparse.ArgumentParser(prog="chatgpt-share-reader", description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("args", nargs=argparse.REMAINDER, help="arguments for the verb; see `read --help`")
    args = parser.parse_args(argv)
    return share.main(args.args, prog=f"chatgpt-share-reader {args.command}")


if __name__ == "__main__":
    sys.exit(main())
