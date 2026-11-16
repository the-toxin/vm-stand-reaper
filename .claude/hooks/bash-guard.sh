#!/usr/bin/env bash

# PreToolUse guard for Bash tool commands. Defense-in-depth only, NOT a security
# boundary (the real guardrail is YC IAM). Reads the Claude Code hook JSON on
# stdin; prints a BLOCKED reason to stderr and exits 2 on first rule match.
set -euo pipefail

command -v jq >/dev/null 2>&1 || exit 0   # fail open, parity with old inline hooks

RAW=$(jq -r '.tool_input.command // empty') || exit 0
[ -z "$RAW" ] && exit 0

# Normalize: collapse all whitespace runs (space/tab/newline/CR) to single
# spaces, trim edges.
CMD=$(printf '%s' "$RAW" | tr -s '[:space:]' ' ')
CMD="${CMD# }"
CMD="${CMD% }"

check() {  # $1 = ERE, $2 = human-readable reason
if printf '%s\n' "$CMD" | grep -qiE -- "$1"; then
    printf 'BLOCKED: %s\n' "$2" >&2
    exit 2
fi
}

check '\brm\b( +-+[a-z-]+)* +-+[a-z]*r[a-z-]*( +-+[a-z-]+)* ["'\'']?(/\*?|~/?\*?|\$\{?HOME\}?\/?\*?)["'\'']?( |$)' \
'recursive rm targeting /, /*, ~ or $HOME'
check '\byc\b[^;|&()<>]*\bdelete\b' \
'yc resource deletion'
check '\bdocker\b[^;|&()<>]*\b(system|image|container|volume|network|builder)\b +prune\b' \
'docker bulk prune'
check '(curl|wget).*\|.*\b(bash|sh|zsh|dash|ksh|python3?|source)\b' \
'pipe downloaded content into a shell or interpreter'

exit 0
