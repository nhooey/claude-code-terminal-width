# terminal-width

A Claude Code mod that tells the model the terminal's width. Before a prompt goes out, when the width Claude Code draws the prompt band at has changed since the model was last told, `hooks/register.ts` adds one line to the conversation. The plugin manifest is `.claude-plugin/plugin.json` and the tests are in `tests/`.

## Build and test

- `nix develop` gives the `mod` tool and installs the project's skills into `.agents/skills/` from the `skills-devshell/` sub-flake.
- `mod check` runs `mod validate`, `mod test` and `mod typecheck` (`claude plugin validate`, `claude plugin test` and `tsc`), with the `claude` on your `PATH`. `mod typecheck` is skipped until Claude Code has loaded the mod once and written its API types to `.claude-plugin/types/`. `mod --help` lists the commands and their options; the tool is `scripts/mod.py`, tested by `scripts/test_mod.py`.
- `nix fmt` formats the repository through treefmt, and `nix flake check` fails on anything unformatted. Neither runs the plugin test or `tsc`, which need the `claude` on your `PATH`.
