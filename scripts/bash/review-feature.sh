#!/usr/bin/env bash
# review-feature.sh - Script for review commands to get feature context and create review outputs
# Usage: ./review-feature.sh [--json] [--review-type TYPE] [--require-spec] [--require-plan] [--require-tasks]
#
# Options:
#   --json            Output JSON format for command parsing
#   --review-type     Type of review (uat, implementation, security, readiness, summary, fix, release-notes)
#   --require-spec    Require spec.md to exist
#   --require-plan    Require implementation-plan.md to exist
#   --require-tasks   Require tasks.md to exist
#   --create-output   Create the output directory/file structure
#
# Outputs JSON with:
#   FEATURE_DIR, FEATURE_NAME, BRANCH_NAME, REVIEW_TYPE, OUTPUT_FILE, OUTPUT_DIR,
#   AVAILABLE_DOCS (list of existing spec files), CONSTITUTION_PATH

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
fi

# Find repo root
find_repo_root() {
    local dir="$PWD"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" ]] || [[ -d "$dir/specs" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

REPO_ROOT="$(find_repo_root)"

# Parse arguments
JSON_OUTPUT=false
REVIEW_TYPE=""
REQUIRE_SPEC=false
REQUIRE_PLAN=false
REQUIRE_TASKS=false
CREATE_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --review-type)
            REVIEW_TYPE="$2"
            shift 2
            ;;
        --require-spec)
            REQUIRE_SPEC=true
            shift
            ;;
        --require-plan)
            REQUIRE_PLAN=true
            shift
            ;;
        --require-tasks)
            REQUIRE_TASKS=true
            shift
            ;;
        --create-output)
            CREATE_OUTPUT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Get current branch name
get_branch_name() {
    if git rev-parse --is-inside-work-tree &>/dev/null; then
        git branch --show-current 2>/dev/null || echo "main"
    else
        echo "main"
    fi
}

BRANCH_NAME="$(get_branch_name)"

# Derive feature directory from branch name
# Branch format: N-short-name (e.g., 1-user-auth, 5-payment-flow)
get_feature_dir() {
    local branch="$1"
    local specs_dir="$REPO_ROOT/specs"
    
    # If specs directory exists, look for matching feature
    if [[ -d "$specs_dir" ]]; then
        # Try exact match first
        if [[ -d "$specs_dir/$branch" ]]; then
            echo "$specs_dir/$branch"
            return 0
        fi
        
        # Try to find feature by branch prefix (N-name pattern)
        local feature_dirs=("$specs_dir"/*/)
        for dir in "${feature_dirs[@]}"; do
            local dirname=$(basename "$dir")
            if [[ "$dirname" == "$branch" ]]; then
                echo "$dir"
                return 0
            fi
        done
        
        # If no match, return expected path
        echo "$specs_dir/$branch"
    else
        # No specs dir, create expected path
        echo "$specs_dir/$branch"
    fi
}

FEATURE_DIR="$(get_feature_dir "$BRANCH_NAME")"
FEATURE_NAME="${BRANCH_NAME#*-}"  # Strip leading number prefix if present

# Define output paths based on review type
get_output_info() {
    local review_type="$1"
    local feature_dir="$2"
    
    case "$review_type" in
        uat)
            echo "$feature_dir/uat|$feature_dir/uat/plan.md"
            ;;
        implementation)
            echo "$feature_dir|$feature_dir/review-implementation.md"
            ;;
        security)
            echo "$feature_dir|$feature_dir/security-review.md"
            ;;
        readiness)
            echo "$feature_dir|$feature_dir/release-readiness.md"
            ;;
        summary)
            echo "$feature_dir/docs|$feature_dir/docs/SUMMARY.md"
            ;;
        fix)
            echo "$feature_dir|$feature_dir/fix-report.md"
            ;;
        release-notes)
            echo "$feature_dir|$feature_dir/release-notes.md"
            ;;
        *)
            echo "$feature_dir|$feature_dir/review-output.md"
            ;;
    esac
}

OUTPUT_INFO="$(get_output_info "$REVIEW_TYPE" "$FEATURE_DIR")"
OUTPUT_DIR="${OUTPUT_INFO%|*}"
OUTPUT_FILE="${OUTPUT_INFO#*|}"

# Check for required files
check_required_files() {
    local errors=()
    
    if [[ "$REQUIRE_SPEC" == true ]] && [[ ! -f "$FEATURE_DIR/spec.md" ]]; then
        errors+=("spec.md not found. Run /speckit.specify first.")
    fi
    
    if [[ "$REQUIRE_PLAN" == true ]] && [[ ! -f "$FEATURE_DIR/implementation-plan.md" ]]; then
        errors+=("implementation-plan.md not found. Run /speckit.plan first.")
    fi
    
    if [[ "$REQUIRE_TASKS" == true ]] && [[ ! -f "$FEATURE_DIR/tasks.md" ]]; then
        errors+=("tasks.md not found. Run /speckit.tasks first.")
    fi
    
    if [[ ${#errors[@]} -gt 0 ]]; then
        if [[ "$JSON_OUTPUT" == true ]]; then
            printf '{"error": true, "messages": ["%s"]}' "$(IFS='","'; echo "${errors[*]}")"
        else
            for err in "${errors[@]}"; do
                echo "ERROR: $err" >&2
            done
        fi
        exit 1
    fi
}

# Build list of available docs
get_available_docs() {
    local docs=()
    
    [[ -f "$FEATURE_DIR/spec.md" ]] && docs+=("spec.md")
    [[ -f "$FEATURE_DIR/implementation-plan.md" ]] && docs+=("implementation-plan.md")
    [[ -f "$FEATURE_DIR/tasks.md" ]] && docs+=("tasks.md")
    [[ -f "$FEATURE_DIR/quickstart.md" ]] && docs+=("quickstart.md")
    [[ -f "$FEATURE_DIR/data-model.md" ]] && docs+=("data-model.md")
    [[ -d "$FEATURE_DIR/checklists" ]] && docs+=("checklists/")
    [[ -d "$FEATURE_DIR/uat" ]] && docs+=("uat/")
    
    echo "${docs[*]}"
}

# Get constitution path
get_constitution_path() {
    local paths=(
        "$REPO_ROOT/.specify/memory/constitution.md"
        "$REPO_ROOT/memory/constitution.md"
    )
    
    for path in "${paths[@]}"; do
        if [[ -f "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    echo ""
}

CONSTITUTION_PATH="$(get_constitution_path)"
AVAILABLE_DOCS="$(get_available_docs)"

# Check required files
check_required_files

# Create output directory if requested
if [[ "$CREATE_OUTPUT" == true ]] && [[ -n "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

# Output results
if [[ "$JSON_OUTPUT" == true ]]; then
    # Build JSON output
    cat <<EOF
{
    "REPO_ROOT": "$REPO_ROOT",
    "FEATURE_DIR": "$FEATURE_DIR",
    "FEATURE_NAME": "$FEATURE_NAME",
    "BRANCH_NAME": "$BRANCH_NAME",
    "REVIEW_TYPE": "$REVIEW_TYPE",
    "OUTPUT_DIR": "$OUTPUT_DIR",
    "OUTPUT_FILE": "$OUTPUT_FILE",
    "CONSTITUTION_PATH": "$CONSTITUTION_PATH",
    "AVAILABLE_DOCS": "$(echo "$AVAILABLE_DOCS" | tr ' ' ',')",
    "SPEC_FILE": "$FEATURE_DIR/spec.md",
    "PLAN_FILE": "$FEATURE_DIR/implementation-plan.md",
    "TASKS_FILE": "$FEATURE_DIR/tasks.md"
}
EOF
else
    echo "Repository Root: $REPO_ROOT"
    echo "Feature Directory: $FEATURE_DIR"
    echo "Feature Name: $FEATURE_NAME"
    echo "Branch: $BRANCH_NAME"
    echo "Review Type: $REVIEW_TYPE"
    echo "Output Directory: $OUTPUT_DIR"
    echo "Output File: $OUTPUT_FILE"
    echo "Constitution: $CONSTITUTION_PATH"
    echo "Available Docs: $AVAILABLE_DOCS"
fi
