#!/bin/bash
# ARIS build + test inside the container. Source is mounted read-only and copied; no secrets are passed in.
node --version
cp -r /src /work && cd /work || exit 2
corepack enable >/dev/null 2>&1
corepack prepare pnpm@10.33.0 --activate >/dev/null 2>&1
pnpm --version
echo "=== INSTALL"
pnpm install --frozen-lockfile > /tmp/install.log 2>&1; rc=$?; tail -30 /tmp/install.log; echo "install_exit=$rc"
[ $rc -ne 0 ] && exit 0
echo "=== BUILD"
pnpm build > /tmp/build.log 2>&1; rc=$?; tail -30 /tmp/build.log; echo "build_exit=$rc"
echo "=== TEST"
pnpm test > /tmp/test.log 2>&1; rc=$?; tail -40 /tmp/test.log; echo "test_exit=$rc"
