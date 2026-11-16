"""Tests for mod's argument parsing and its pure parts.

Run with `python3 -m unittest discover -s scripts`; `nix flake check` runs
them as the `mod-tests` check.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import mod


def parse(*argv: str):
    return mod.build_parser().parse_args(argv)


class ParserTest(unittest.TestCase):
    def exit_status(self, *argv: str):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            parse(*argv)
        return caught.exception.code

    def test_each_command_parses(self):
        for command in ("check", "validate", "test", "typecheck"):
            with self.subTest(command=command):
                self.assertEqual(parse(command).command, command)

    def test_a_command_is_required(self):
        self.assertEqual(self.exit_status(), mod.EXIT_USAGE)

    def test_an_unknown_command_is_a_usage_error(self):
        self.assertEqual(self.exit_status("deploy"), mod.EXIT_USAGE)

    def test_directory_and_dry_run_options(self):
        args = parse("-C", "/tmp/x", "--dry-run", "check")
        self.assertEqual((args.directory, args.dry_run), (Path("/tmp/x"), True))

    def test_options_default_to_the_working_directory_and_running(self):
        args = parse("test")
        self.assertEqual((args.directory, args.dry_run), (Path.cwd(), False))

    def test_help_lists_every_command_and_option(self):
        text = mod.build_parser().format_help()
        for token in ("check", "validate", "test", "typecheck", "--directory", "--dry-run"):
            with self.subTest(token=token):
                self.assertIn(token, text)


class PlanTest(unittest.TestCase):
    def argvs(self, command, types_present):
        return [s.argv for s in mod.plan(command, types_present)]

    def test_check_runs_validate_test_then_tsc(self):
        self.assertEqual(
            self.argvs("check", True),
            [
                ("claude", "plugin", "validate", "."),
                ("claude", "plugin", "test", "."),
                ("tsc", "-p", "."),
            ],
        )

    def test_check_skips_tsc_without_types_and_carries_on(self):
        last = mod.plan("check", False)[-1]
        self.assertEqual((last.name, last.fatal), ("typecheck", False))
        self.assertIsNotNone(last.skip)

    def test_typecheck_alone_fails_without_types(self):
        (step,) = mod.plan("typecheck", False)
        self.assertTrue(step.fatal)

    def test_single_commands_run_one_step(self):
        self.assertEqual(self.argvs("validate", False), [("claude", "plugin", "validate", ".")])
        self.assertEqual(self.argvs("test", False), [("claude", "plugin", "test", ".")])


class MissingProgramsTest(unittest.TestCase):
    def test_reports_each_missing_program_once_and_ignores_skipped_steps(self):
        steps = mod.plan("check", False)
        self.assertEqual(mod.missing_programs(steps, lambda _: None), ("claude",))

    def test_nothing_missing_when_all_resolve(self):
        steps = mod.plan("check", True)
        self.assertEqual(mod.missing_programs(steps, lambda p: f"/bin/{p}"), ())


class FindRootTest(unittest.TestCase):
    def test_finds_the_manifest_above_a_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / mod.MANIFEST).parent.mkdir()
            (root / mod.MANIFEST).write_text("{}")
            (root / "hooks").mkdir()
            self.assertEqual(mod.find_root(root / "hooks"), root)

    def test_none_without_a_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(mod.find_root(Path(tmp).resolve()))


class RunStepsTest(unittest.TestCase):
    def run_quietly(self, steps, dry_run=True):
        with contextlib.redirect_stderr(io.StringIO()):
            return mod.run_steps(steps, Path("."), dry_run)

    def test_a_fatal_skip_fails(self):
        self.assertEqual(self.run_quietly(mod.plan("typecheck", False)), mod.EXIT_FAILED)

    def test_a_dry_run_of_check_without_types_passes(self):
        self.assertEqual(self.run_quietly(mod.plan("check", False)), mod.EXIT_OK)


if __name__ == "__main__":
    unittest.main()
