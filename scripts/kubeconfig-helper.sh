#!/usr/bin/env bash
set -euo pipefail

# Minimal helper to record a kubeconfig path for use by the Kubernetes MCP
# server (remote or local clusters). It writes KUBECONFIG_PATH into .env.

usage() {
  cat <<EOF
Usage: $0 [command]

Commands:
  import /path/to/config  Store absolute kubeconfig path into .env as KUBECONFIG_PATH
  show                    Print the stored path from .env (if any)
  print                   Print contexts using the stored kubeconfig path

Examples:
  $0 import /tmp/kubeconfig
EOF
}

env_file() { echo "${ENV_FILE:-.env}"; }

write_kubeconfig_path() {
  local abs="$1"
  local f
  f="$(env_file)"
  touch "$f"
  local tmp
  tmp="$(mktemp)"
  awk -v val="$abs" 'BEGIN{done=0} {if($0 ~ /^KUBECONFIG_PATH=/){print "KUBECONFIG_PATH=" val; done=1} else print} END{if(!done) print "KUBECONFIG_PATH=" val}' "$f" > "$tmp"
  mv "$tmp" "$f"
  echo "Saved KUBECONFIG_PATH=$abs into $f"
}

case "${1:-}" in
  import)
    shift || true
    [[ -n "${1:-}" && -f "$1" ]] || { echo "Provide a valid kubeconfig path" >&2; exit 1; }
    abs_path="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
    write_kubeconfig_path "$abs_path"
    ;;
  show)
    if grep -q '^KUBECONFIG_PATH=' "$(env_file)" 2>/dev/null; then
      grep '^KUBECONFIG_PATH=' "$(env_file)"
    else
      echo "KUBECONFIG_PATH not set in $(env_file)"
    fi
    ;;
  print)
    if grep -q '^KUBECONFIG_PATH=' "$(env_file)" 2>/dev/null; then
      path="$(grep '^KUBECONFIG_PATH=' "$(env_file)" | cut -d'=' -f2-)"
      kubectl --kubeconfig "$path" config get-contexts
    else
      echo "KUBECONFIG_PATH not set in $(env_file). Use: $0 import /path/to/kubeconfig" >&2
      exit 1
    fi
    ;;
  *)
    usage
    ;;
esac

