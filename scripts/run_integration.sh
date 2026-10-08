#!/usr/bin/env bash
# Run the integration test (full pipeline on test_data) and print the result.
# With --commit, also record it in an empty commit pushed to GitHub: the title
# says whether the test passed or failed, and the message gives the details.
#
# Usage: scripts/run_integration.sh [--commit] [config.yaml]
#   config.yaml   Config to run with, e.g. your own Singularity config
#                 (default: the packaged default_docker.yaml).
#   --commit      Commit the result and push it to the upstream of the
#                 current branch.
#
# The result commit describes the commit that was tested, i.e. its parent.
# To list the results: git log --grep "Integration testing"
set -uo pipefail

commit=false
config=""
for arg in "$@"; do
    case "$arg" in
        --commit) commit=true ;;
        -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
# Check before the (long) run that the result commit can be pushed.
if $commit && ! git rev-parse --abbrev-ref '@{upstream}' > /dev/null 2>&1; then
    echo "--commit needs a branch that is pushed to GitHub:" \
        "run 'git push -u <remote> <branch>' first."
    exit 1
fi

sha=$(git rev-parse --short HEAD)
out_dir="${TMPDIR:-/tmp}/fetpype_integration/$sha"
rm -rf "$out_dir"
mkdir -p "$out_dir"
log="$out_dir/pytest.log"
echo "Running the integration test on $sha, outputs in $out_dir"

start=$(date +%s)
pytest tests/integration --integration -v \
    ${config:+--integration-config "$config"} \
    --basetemp="$out_dir/runs" 2>&1 | tee "$log"
code=${PIPESTATUS[0]}
minutes=$(( ($(date +%s) - start) / 60 ))

if [ "$code" -eq 0 ]; then
    title="✅ Integration testing passed"
    result="✅ passed"
else
    title="❌ Integration testing failed"
    result="❌ failed"
fi

gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
message="$title

| Result        | $result |
| Tested commit | $sha |
| Date          | $(date +%F) |
| Version       | $(python -c "import fetpype; print(fetpype.__version__)") |
| Config        | $(basename "${config:-default_docker.yaml}") |
| GPU           | ${gpu:-no GPU found} |
| Duration      | $minutes min |"

# On failure, add pytest's summary of what failed.
if [ "$code" -ne 0 ]; then
    failures=$(grep -E "^(FAILED|ERROR) " "$log")
    message="$message

${failures:-pytest exited with code $code, see the log.}"
fi

echo
echo "$message"
echo
if $commit; then
    git commit -q --allow-empty -m "$message"
    echo "Recorded in commit $(git rev-parse --short HEAD)."
    if git push -q; then
        echo "Pushed to $(git rev-parse --abbrev-ref '@{upstream}')."
    else
        echo "Could not push the result commit: push it with 'git push'" \
            "(or 'git push -u <remote> <branch>' if the branch has no upstream)."
        [ "$code" -eq 0 ] && code=1
    fi
fi
echo "Log and outputs: $out_dir"
exit "$code"
