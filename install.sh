#!/usr/bin/env bash
# Install the FlowForge MCP server, the agent skills (`flowforge`, `goal-based-voice-agent`) and the /ff-*
# slash commands for Claude Code, Codex and Claude Desktop (macOS / Linux).
#
#   FLOWFORGE_API_KEY=ff_live_... ./install.sh                  # first install
#   FLOWFORGE_API_KEY=ff_live_... ./install.sh --name flowforge-acme --server-only
#   ./install.sh --update                                       # after git pull
#
# The key is read from FLOWFORGE_API_KEY, or prompted for (hidden) when run in a
# terminal. It is written only into each client's own MCP config, never printed.
# See INSTALL.md for what every step does and how to undo it.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_NAME="flowforge"
CLIENTS="auto"
MODE="install"            # install | update
INSTALL_SKILL=1
REPLACE=0
VENV_DIR="${HOME}/.flowforge-mcp/venv"
SERVERS_FILE="${HOME}/.config/flowforge/servers.md"

usage() {
  cat <<'USAGE'
Usage: ./install.sh [options]

  --name NAME        MCP server name to register (default: flowforge). Use
                     flowforge-<org> for each additional organization's key.
  --clients LIST     Comma list of claude,codex,desktop (default: every client
                     found on this machine).
  --server-only      Register the server only; skip the skills and slash commands.
  --replace          Replace an existing server entry with the same name.
  --update           Reinstall the package, skills and commands; leave client
                     registrations and keys untouched.
  -h, --help         Show this help.

Environment: FLOWFORGE_API_KEY (required unless --update; prompted for when
interactive), FLOWFORGE_BASE_URL (optional override).
USAGE
}

say()  { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --name) SERVER_NAME="${2:?--name needs a value}"; shift 2 ;;
    --clients) CLIENTS="${2:?--clients needs a value}"; shift 2 ;;
    --server-only) INSTALL_SKILL=0; shift ;;
    --replace) REPLACE=1; shift ;;
    --update) MODE="update"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

case "$SERVER_NAME" in
  *[!A-Za-z0-9_-]*|"") die "--name may contain only letters, digits, '-' and '_'" ;;
esac

# --- 1. Install the Python package -------------------------------------------

install_package() {
  if command -v uv >/dev/null 2>&1; then
    say "Installing flowforge-mcp with uv"
    local log
    log="$(uv tool install --force --reinstall "$REPO_DIR" 2>&1)" || die "uv tool install failed:
$log"
    BIN="$(uv tool dir --bin)/flowforge-mcp"
    PY="$(uv tool dir)/flowforge-mcp/bin/python"
  else
    local py=""
    for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
      if command -v "$candidate" >/dev/null 2>&1 \
        && "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
        py="$candidate"; break
      fi
    done
    [ -n "$py" ] || die "need uv (https://docs.astral.sh/uv/) or Python 3.10+"
    say "Installing flowforge-mcp into $VENV_DIR"
    [ -x "$VENV_DIR/bin/python" ] || "$py" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade --force-reinstall --no-deps "$REPO_DIR"
    "$VENV_DIR/bin/python" -m pip install --quiet "$REPO_DIR"
    BIN="$VENV_DIR/bin/flowforge-mcp"
    PY="$VENV_DIR/bin/python"
  fi
  [ -x "$BIN" ] || die "install finished but $BIN is missing"
}

# --- 2. Copy the skill and slash commands ------------------------------------

# Backups go outside the skills folder: a copy left beside the skill would be
# loaded as a second "flowforge" skill.
BACKUP_DIR="$HOME/.flowforge-mcp/backups/$(date +%Y%m%d%H%M%S)"

backup_if_different() {  # $1 = existing path, $2 = new source, $3 = backup label
  if [ -e "$1" ] && ! diff -rq "$1" "$2" >/dev/null 2>&1; then
    local backup="$BACKUP_DIR/$3"
    mkdir -p "$(dirname "$backup")"
    mv "$1" "$backup"
    say "Backed up previous $(basename "$1") to $backup"
  elif [ -e "$1" ]; then
    rm -rf -- "$1"   # identical copy from a previous install
  fi
}

install_skill() {
  local src name root dest names=()
  for src in "$REPO_DIR"/skills/*/; do
    src="${src%/}"
    name="$(basename "$src")"
    names+=("$name")
    for root in "$HOME/.claude/skills" "$HOME/.agents/skills"; do   # Claude Code, Codex
      dest="$root/$name"
      mkdir -p "$root"
      backup_if_different "$dest" "$src" "$(basename "$(dirname "$root")" | sed 's/^\.//')-skills/$name"
      cp -R "$src" "$dest"
    done
  done
  say "Skills installed to ~/.claude/skills (Claude Code) and ~/.agents/skills (Codex): ${names[*]}"

  mkdir -p "$HOME/.claude/commands"
  local cmd
  for cmd in "$REPO_DIR"/commands/ff-*.md; do
    backup_if_different "$HOME/.claude/commands/$(basename "$cmd")" "$cmd" "commands/$(basename "$cmd")"
    cp "$cmd" "$HOME/.claude/commands/"
  done
  say "Slash commands installed: ~/.claude/commands/ff-*.md"
}

# --- 3. Read and verify the API key ------------------------------------------

read_key() {
  KEY="${FLOWFORGE_API_KEY:-}"
  if [ -z "$KEY" ] && [ -t 0 ]; then
    printf 'FlowForge API key (input hidden): '
    IFS= read -rs KEY; printf '\n'
  fi
  [ -n "$KEY" ] || die "no API key. Set FLOWFORGE_API_KEY (create one in the FlowForge dashboard under Settings -> API Keys)." 2
  case "$KEY" in ff_live_*|ff_test_*) ;; *) warn "key does not start with ff_live_; continuing" ;; esac
}

verify_key() {
  local result
  if ! result="$(FLOWFORGE_API_KEY="$KEY" "$BIN" --check 2>&1)"; then
    die "the key was rejected, the API is unreachable, or the server failed to start:
$result"
  fi
  result="$(printf '%s\n' "$result" | tail -n 1)"
  ORG_NAME="$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1]).get("organization") or "unknown")' "$result")"
  ORG_ID="$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1]).get("organization_id") or "")' "$result")"
  TOOL_COUNT="$("$PY" -c 'import json,sys; print(json.loads(sys.argv[1])["tools"])' "$result")"
  say "Key works: organization \"$ORG_NAME\", $TOOL_COUNT tools"
}

# --- 4. Register the server with each client ---------------------------------

env_args() {  # prints KEY=VALUE pairs for the server environment
  printf 'FLOWFORGE_API_KEY=%s\n' "$KEY"
  if [ -n "${FLOWFORGE_BASE_URL:-}" ]; then printf 'FLOWFORGE_BASE_URL=%s\n' "$FLOWFORGE_BASE_URL"; fi
}

register_claude() {
  if claude mcp get "$SERVER_NAME" >/dev/null 2>&1; then
    if [ "$REPLACE" -eq 0 ]; then
      warn "Claude Code already has a server named $SERVER_NAME; left as is (use --replace to overwrite)"
      return
    fi
    claude mcp remove -s user "$SERVER_NAME" >/dev/null 2>&1 || claude mcp remove "$SERVER_NAME" >/dev/null
  fi
  local args=() pair
  while IFS= read -r pair; do args+=(-e "$pair"); done < <(env_args)
  claude mcp add "$SERVER_NAME" -s user "${args[@]}" -- "$BIN" >/dev/null
  say "Registered with Claude Code (user scope) as $SERVER_NAME"
}

register_codex() {
  if codex mcp get "$SERVER_NAME" >/dev/null 2>&1; then
    if [ "$REPLACE" -eq 0 ]; then
      warn "Codex already has a server named $SERVER_NAME; left as is (use --replace to overwrite)"
      return
    fi
    codex mcp remove "$SERVER_NAME" >/dev/null
  fi
  local args=() pair
  while IFS= read -r pair; do args+=(--env "$pair"); done < <(env_args)
  codex mcp add "$SERVER_NAME" "${args[@]}" -- "$BIN" >/dev/null
  say "Registered with Codex as $SERVER_NAME"
}

desktop_config_path() {
  case "$(uname -s)" in
    Darwin) printf '%s\n' "$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
    *) printf '%s\n' "${XDG_CONFIG_HOME:-$HOME/.config}/Claude/claude_desktop_config.json" ;;
  esac
}

DESKTOP_PY='
import json, os, shutil, sys, time
path, name, command, replace, env_lines = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == "1", sys.argv[5]
env = dict(line.split("=", 1) for line in env_lines.splitlines() if "=" in line)
config = {}
if os.path.exists(path):
    with open(path) as handle:
        config = json.load(handle)
servers = config.get("mcpServers", {})
if name in servers and not replace:
    print("exists")
    sys.exit(0)
if os.path.exists(path):
    shutil.copy2(path, path + ".bak-" + time.strftime("%Y%m%d%H%M%S"))
updated = {**config, "mcpServers": {**servers, name: {"command": command, "env": env}}}
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as handle:
    json.dump(updated, handle, indent=2)
    handle.write("\n")
print("added")
'

register_desktop() {
  local config; config="$(desktop_config_path)"
  local status
  status="$("$PY" -c "$DESKTOP_PY" "$config" "$SERVER_NAME" "$BIN" "$REPLACE" "$(env_args)")"
  if [ "$status" = "exists" ]; then
    warn "Claude Desktop already has a server named $SERVER_NAME; left as is (use --replace to overwrite)"
  else
    say "Registered with Claude Desktop as $SERVER_NAME (restart the app to load it)"
  fi
}

register_clients() {
  local wanted="$CLIENTS" found=0
  if [ "$wanted" = "auto" ]; then
    wanted=""
    command -v claude >/dev/null 2>&1 && wanted="$wanted,claude"
    command -v codex  >/dev/null 2>&1 && wanted="$wanted,codex"
    [ -d "$(dirname "$(desktop_config_path)")" ] && wanted="$wanted,desktop"
  fi
  local client
  IFS=',' read -ra list <<< "$wanted"
  for client in "${list[@]}"; do
    case "$client" in
      "") ;;
      claude)  command -v claude >/dev/null 2>&1 || die "claude CLI not found"; register_claude; found=1 ;;
      codex)   command -v codex  >/dev/null 2>&1 || die "codex CLI not found"; register_codex; found=1 ;;
      desktop) register_desktop; found=1 ;;
      *) die "unknown client: $client (use claude, codex, desktop)" ;;
    esac
  done
  [ "$found" -eq 1 ] || warn "no MCP client found; add the server by hand (see INSTALL.md, 'Other clients'): command $BIN, env FLOWFORGE_API_KEY"
}

record_server() {  # keeps ~/.config/flowforge/servers.md as the name -> org map the skill reads
  mkdir -p "$(dirname "$SERVERS_FILE")"
  "$PY" - "$SERVERS_FILE" "$SERVER_NAME" "$ORG_NAME" "$ORG_ID" <<'PYCODE'
import os, sys, time
path, name, org, org_id = sys.argv[1:5]
header = "# FlowForge MCP servers on this machine\n\nServer name -> organization (written by install.sh).\n\n"
lines = []
if os.path.exists(path):
    with open(path) as handle:
        lines = [l for l in handle.read().splitlines() if l.startswith("- ")]
lines = [l for l in lines if not l.startswith(f"- `{name}` ")]
lines.append(f"- `{name}` -> {org} (org id {org_id or 'unknown'}), added {time.strftime('%Y-%m-%d')}")
with open(path, "w") as handle:
    handle.write(header + "\n".join(sorted(lines)) + "\n")
PYCODE
}

# --- main ----------------------------------------------------------------------

if [ "$MODE" = "install" ]; then read_key; fi
install_package
if [ "$INSTALL_SKILL" -eq 1 ]; then install_skill; fi

if [ "$MODE" = "update" ]; then
  say "Updated. Restart Claude Code / Codex / Claude Desktop sessions to load the new version."
  exit 0
fi

verify_key
register_clients
record_server
if [ "$SERVER_NAME" != "flowforge" ]; then
  warn "the /ff-* slash commands call the server named 'flowforge'; with $SERVER_NAME, ask the agent directly instead"
fi
say "Done. Restart Claude Code / Codex / Claude Desktop, then ask: \"Using FlowForge, list my assistants.\""
