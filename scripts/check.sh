# Validate, test and type-check the mod in the current directory.
if ! command -v claude >/dev/null; then
  echo "check: claude isn't on PATH" >&2
  exit 1
fi
claude plugin validate .
claude plugin test .
if [ -f .claude-plugin/types/tsconfig.json ]; then
  tsc -p .
else
  echo "check: skipping tsc; load the mod in Claude Code once to lay its types" >&2
fi
