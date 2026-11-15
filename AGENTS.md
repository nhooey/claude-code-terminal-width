# terminal-width

A Claude Code mod that tells the model the terminal's width. Before a prompt goes out, when the width Claude Code draws the prompt band at has changed since the model was last told, `hooks/register.ts` adds one line to the conversation. The plugin manifest is `.claude-plugin/plugin.json` and the tests are in `tests/`.

## Build and test

- `nix develop` gives TypeScript and installs the project's skills into `.agents/skills/` from the `skills-devshell/` sub-flake.
- `nix run .#check` runs `claude plugin validate`, `claude plugin test` and `tsc`, with the `claude` on your `PATH`. `tsc` is skipped until Claude Code has loaded the mod once and written its API types to `.claude-plugin/types/`.
- `nix flake check` and `nix fmt` check and format the flake.
