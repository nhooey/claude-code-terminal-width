"""mod: validate, test and type-check the terminal-width Claude Code mod.

Each command runs from the mod's root, the nearest directory at or above
the working directory (or --directory) that holds .claude-plugin/plugin.json.
`claude` comes from PATH: it is unfree and changes daily, so the dev shell
doesn't pin it.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence

PROG = "mod"
MANIFEST = Path(".claude-plugin") / "plugin.json"
TYPES_CONFIG = Path(".claude-plugin") / "types" / "tsconfig.json"

# Exit statuses, beyond a failed step's own status.
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 127

NO_TYPES = (
    "Claude Code hasn't written the mod's API types to "
    f"{TYPES_CONFIG.parent}/ yet; load the mod in Claude Code once"
)


@dataclass(frozen=True)
class Step:
    """One command to run, or, with `skip` set, the reason it won't run.

    A skipped step with `fatal` set fails the command; without it, the
    command carries on to the next step.
    """

    name: str
    argv: tuple[str, ...]
    skip: Optional[str] = None
    fatal: bool = False


def validate_step() -> Step:
    return Step("validate", ("claude", "plugin", "validate", "."))


def test_step() -> Step:
    return Step("test", ("claude", "plugin", "test", "."))


def typecheck_step(types_present: bool, required: bool) -> Step:
    """tsc against Claude Code's types; skipped, or failed when `required`."""
    if types_present:
        return Step("typecheck", ("tsc", "-p", "."))
    return Step("typecheck", (), skip=NO_TYPES, fatal=required)


def plan(command: str, types_present: bool) -> tuple[Step, ...]:
    """The steps `command` runs, in order."""
    plans: dict[str, Callable[[], tuple[Step, ...]]] = {
        "check": lambda: (
            validate_step(),
            test_step(),
            typecheck_step(types_present, required=False),
        ),
        "validate": lambda: (validate_step(),),
        "test": lambda: (test_step(),),
        "typecheck": lambda: (typecheck_step(types_present, required=True),),
    }
    return plans[command]()


def find_root(start: Path) -> Optional[Path]:
    """The nearest directory at or above `start` holding the plugin manifest."""
    return next(
        (d for d in (start, *start.parents) if (d / MANIFEST).is_file()),
        None,
    )


def missing_programs(steps: Iterable[Step], which: Callable[[str], Optional[str]]) -> tuple[str, ...]:
    """Programs the runnable steps need that aren't on PATH, deduplicated."""
    programs = dict.fromkeys(s.argv[0] for s in steps if s.skip is None and s.argv)
    return tuple(p for p in programs if which(p) is None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Validate, test and type-check the terminal-width mod.",
        epilog="Exit status: 0 when every step passes, a failed step's own "
        "status, 1 for a required step that can't run, 2 for a usage "
        "error, 127 when a program isn't on PATH.",
    )
    parser.add_argument(
        "-C",
        "--directory",
        type=Path,
        default=Path.cwd(),
        help="find the mod's root from DIRECTORY instead of the working directory",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print the commands instead of running them",
    )
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)
    commands.add_parser(
        "check",
        help="run validate, test and typecheck; typecheck is skipped until the types exist",
        description="Run validate, test and typecheck, stopping at the first failure. "
        "typecheck is skipped, not failed, until Claude Code has written the types.",
    )
    commands.add_parser(
        "validate",
        help="run `claude plugin validate` on the manifest",
        description="Run `claude plugin validate .` from the mod's root.",
    )
    commands.add_parser(
        "test",
        help="run the mod's tests with `claude plugin test`",
        description="Run `claude plugin test .` from the mod's root.",
    )
    commands.add_parser(
        "typecheck",
        help="type-check the mod with tsc against Claude Code's API types",
        description="Run `tsc -p .` from the mod's root. Fails until Claude Code "
        "has loaded the mod once and written its types.",
    )
    return parser


def run_steps(steps: Sequence[Step], root: Path, dry_run: bool) -> int:
    """Run each step from `root`, stopping at the first that fails."""
    for step in steps:
        if step.skip is not None:
            verdict = "can't run" if step.fatal else "skipped"
            print(f"{PROG} {step.name}: {verdict}: {step.skip}", file=sys.stderr)
            if step.fatal:
                return EXIT_FAILED
            continue
        print(f"{PROG} {step.name}: {' '.join(step.argv)}", file=sys.stderr)
        if dry_run:
            continue
        status = subprocess.run(step.argv, cwd=root).returncode
        if status != EXIT_OK:
            return status
    return EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    start = args.directory.resolve()
    root = find_root(start)
    if root is None:
        print(f"{PROG}: no {MANIFEST} at or above {start}", file=sys.stderr)
        return EXIT_USAGE
    steps = plan(args.command, (root / TYPES_CONFIG).is_file())
    missing = () if args.dry_run else missing_programs(steps, shutil.which)
    if missing:
        print(f"{PROG}: not on PATH: {', '.join(missing)}", file=sys.stderr)
        return EXIT_NOT_FOUND
    return run_steps(steps, root, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
