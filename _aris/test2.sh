#!/bin/bash
cp -r /src /work && cd /work || exit 2
corepack enable >/dev/null 2>&1; corepack prepare pnpm@10.33.0 --activate >/dev/null 2>&1
pnpm install --frozen-lockfile >/dev/null 2>&1 && pnpm build >/dev/null 2>&1 || { echo build_failed; exit 0; }
echo "git=$(git --version 2>&1)"
echo "=== RUN 1 (no git identity)"
pnpm exec vitest run 2>&1 | grep -E "FAIL|✗|×|Test Files|Tests  " | sed 's/\x1b\[[0-9;]*m//g' | sort -u | head -30
git config --global user.email ci@example.invalid; git config --global user.name ci
echo "=== RUN 2 (git identity set)"
pnpm exec vitest run 2>&1 | grep -E "FAIL|Test Files|Tests  " | sed 's/\x1b\[[0-9;]*m//g' | sort -u | head -30
