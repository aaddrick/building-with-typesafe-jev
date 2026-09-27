#!/usr/bin/env bash
# Read the docs copies that docs-cache.yml keeps as workflow artifacts.
#
# A copy is named by a ref, the JSON kept in the DOCS_LATEST and
# DOCS_SKILL_REVIEWED repository variables:
#   {"run_id": 123, "artifact_id": 456, "sha256": "<hex>", "pages": 111}
#
#   docs_artifact.sh field REF KEY       print one key of REF, or nothing
#   docs_artifact.sh expires REF         print the artifact's expiry, or "gone"
#   docs_artifact.sh download REF DEST   write the copy's llms-full.txt to DEST;
#                                        exit 1 if REF is empty or the artifact expired
#
# Needs GH_TOKEN with actions: read, and GITHUB_REPOSITORY.
set -euo pipefail

field() {
  [[ -n "${1:-}" ]] || return 0
  jq -r --arg k "$2" '.[$k] // empty' <<< "$1" 2>/dev/null || true
}

case "${1:-}" in
  field)
    field "${2:-}" "$3"
    ;;
  expires)
    id=$(field "${2:-}" artifact_id)
    [[ -n "$id" ]] || { echo gone; exit 0; }
    gh api "repos/$GITHUB_REPOSITORY/actions/artifacts/$id" \
      --jq 'if .expired then "gone" else .expires_at end' 2>/dev/null || echo gone
    ;;
  download)
    id=$(field "${2:-}" artifact_id)
    [[ -n "$id" ]] || exit 1
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' EXIT
    gh api "repos/$GITHUB_REPOSITORY/actions/artifacts/$id/zip" > "$tmp/docs.zip" 2>/dev/null || exit 1
    unzip -p "$tmp/docs.zip" llms-full.txt > "$3"
    want=$(field "$2" sha256)
    if [[ -n "$want" && "$(sha256sum "$3" | cut -d' ' -f1)" != "$want" ]]; then
      echo "artifact $id does not match its sha256" >&2
      exit 1
    fi
    ;;
  *)
    echo "usage: $0 field REF KEY | expires REF | download REF DEST" >&2
    exit 2
    ;;
esac
