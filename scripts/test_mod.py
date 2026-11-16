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
from unittest import mock

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


class MainTest(unittest.TestCase):
    """The exit statuses `mod --help` promises, through main()."""

    def main_quietly(self, *argv: str):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            status = mod.main(argv)
        return status, stderr.getvalue()

    def mod_root(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        (root / mod.MANIFEST).parent.mkdir()
        (root / mod.MANIFEST).write_text("{}")
        return root

    def test_no_manifest_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            status, err = self.main_quietly("-C", tmp, "-n", "validate")
        self.assertEqual(status, mod.EXIT_USAGE)
        self.assertIn(str(mod.MANIFEST), err)

    def test_a_program_missing_from_path_is_not_found(self):
        root = self.mod_root()
        with mock.patch.object(mod.shutil, "which", lambda _: None):
            status, err = self.main_quietly("-C", str(root), "validate")
        self.assertEqual(status, mod.EXIT_NOT_FOUND)
        self.assertIn("not on PATH: claude", err)

    def test_a_dry_run_needs_nothing_on_path_and_prints_each_command(self):
        root = self.mod_root()
        with mock.patch.object(mod.shutil, "which", lambda _: None):
            status, err = self.main_quietly("-C", str(root), "-n", "check")
        self.assertEqual(status, mod.EXIT_OK)
        self.assertIn("mod validate: claude plugin validate .", err)
        self.assertIn("mod test: claude plugin test .", err)
        self.assertIn("mod typecheck: skipped", err)

    def test_typecheck_without_types_fails(self):
        root = self.mod_root()
        status, err = self.main_quietly("-C", str(root), "-n", "typecheck")
        self.assertEqual(status, mod.EXIT_FAILED)
        self.assertIn("can't run", err)

    def test_a_failed_step_stops_the_run_with_its_own_status(self):
        root = self.mod_root()
        calls = []

        def run(argv, cwd):
            calls.append((argv, cwd))
            return mock.Mock(returncode=3)

        with mock.patch.object(mod.shutil, "which", lambda p: f"/bin/{p}"), mock.patch.object(
            mod.subprocess, "run", run
        ):
            status, _ = self.main_quietly("-C", str(root / ".claude-plugin"), "check")
        self.assertEqual(status, 3)
        self.assertEqual(calls, [(("claude", "plugin", "validate", "."), root)])


if __name__ == "__main__":
    unittest.main()
