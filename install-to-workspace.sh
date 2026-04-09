#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${HOME}/.openclaw/workspace/skills"

mkdir -p "${TARGET}"

for skill in \
  scalper-precheck \
  scalper-playbook \
  scalper-executor \
  scalper-position-watch
do
  rsync -a --delete \
    --exclude='.DS_Store' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    "${ROOT}/${skill}/" \
    "${TARGET}/${skill}/"
done

echo "Installed custom scalper skills to: ${TARGET}"
echo "Verify with: node openclaw.mjs skills list | rg 'scalper-(precheck|playbook|executor|position-watch)'"
