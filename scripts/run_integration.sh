#!/usr/bin/env bash
# Run the integration test (full pipeline on test_data) and report the result
# as a commit status on GitHub, shown with the other checks of the commit/PR.
#
# Usage: scripts/run_integration.sh [--no-report] [config.yaml]
#   config.yaml   Config to run with, e.g. your own Singularity config
#                 (default: the packaged default_docker.yaml).
#   --no-report   Only run the test, do not post the result on GitHub.
#
# Reporting needs the GitHub CLI (gh), logged in with write access to the
# repository (FETPYPE_REPO, default: fetpype/fetpype).
set -uo pipefail

REPO="${FETPYPE_REPO:-fetpype/fetpype}"
CONTEXT="integration (local)"

report=true
config=""
for arg in "$@"; do
    case "$arg" in
        --no-report) report=false ;;
        -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) config="$arg" ;;
    esac
done

cd "$(git rev-parse --show-toplevel)" || exit 1

# The result is attached to a commit, so the code must match it exactly.
if ! git diff --quiet HEAD \
    || [ -n "$(git ls-files --others --exclude-standard fetpype tests)" ]; then
    echo "Commit your changes first: the result is attached to the current commit."
    exit 1
fi
if $report && ! gh auth status > /dev/null 2>&1; then
    echo "gh is not logged in: run 'gh auth login', or use --no-report."
    exit 1
fi

sha=$(git rev-parse HEAD)
out_dir="${TMPDIR:-/tmp}/fetpype_integration/${sha:0:8}"
rm -rf "$out_dir"
mkdir -p "$out_dir"
log="$out_dir/pytest.log"
echo "Running the integration test on ${sha:0:8}, outputs in $out_dir"

start=$(date +%s)
pytest tests/integration --integration -v \
    ${config:+--integration-config "$config"} \
    --basetemp="$out_dir/runs" 2>&1 | tee "$log"
code=${PIPESTATUS[0]}
minutes=$(( ($(date +%s) - start) / 60 ))

state=$([ "$code" -eq 0 ] && echo success || echo failure)
gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
description="$(date +%F), ${minutes} min, $(basename "${config:-default_docker.yaml}"), ${gpu:-no GPU found}"
echo
echo "Integration test: $state ($description)"
echo "Log: $log"

if $report; then
    if gh api "repos/$REPO/statuses/$sha" \
        -f state="$state" -f context="$CONTEXT" \
        -f description="${description:0:140}" > /dev/null; then
        echo "Reported as '$CONTEXT' on $REPO@${sha:0:8}."
    else
        echo "Could not report the result on $REPO: is ${sha:0:8} pushed there (or in an open PR)?"
        [ "$code" -eq 0 ] && code=1
    fi
fi
exit "$code"
