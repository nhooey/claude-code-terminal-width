# terminal-width

A Claude Code mod that tells the model how wide the terminal is.

The model can't measure the terminal itself: in its Bash shell `$COLUMNS` is 0 and `tput cols` says 80 whatever the window is, so it guesses, and writes tables that wrap badly. This mod reads the width Claude Code draws the prompt band at, and before a prompt goes out, when the width has changed since the model was last told, adds one line to the conversation: "The terminal is N columns wide." The note goes in the conversation rather than the system prompt, since a thread's system prompt is fixed once sent.

It draws nothing and changes nothing else.

## Install

```text
/plugin marketplace add nhooey/claude-code-terminal-width
/plugin install terminal-width@claude-code-terminal-width
```

## Develop

`nix develop` gives TypeScript, then `nix run .#check` runs `claude plugin validate`, `claude plugin test` and `tsc`. It uses the `claude` on your `PATH`, and `tsc` needs the API types Claude Code writes to `.claude-plugin/types/` the first time it loads the mod.
