#!/usr/bin/env bash
#
# run_benchmark.sh - Multi-model benchmark testing workflow
#
# This script orchestrates testing of multiple LLM models by:
# 1. Reading model configurations from models_config.yaml
# 2. Running evaluate_mcp.py for each enabled model
# 3. Saving results to test_results/<model_id>/ directories
# 4. Optionally aggregating results into summary tables and plots
#
# Environment Variables:
#   RESUME=true         - Skip models that already have completed results
#   MODELS_CONFIG       - Path to models_config.yaml (default: mcp_llm_test/models_config.yaml)
#   OUTPUT_DIR          - Base directory for results (default: test_results)
#   CONCURRENCY         - Number of concurrent test executions per model (default: 1)
#   TIMEOUT             - Timeout per test case in seconds (default: 600)
#   ANALYZE             - Generate summary tables and plots after testing (default: true)
#
# Usage:
#   # Fresh run (all models)
#   ./run_benchmark.sh
#
#   # Resume previous run (skip completed models)
#   RESUME=true ./run_benchmark.sh
#
#   # Custom configuration
#   MODELS_CONFIG=custom_models.yaml OUTPUT_DIR=my_results ./run_benchmark.sh
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_CONFIG="${MODELS_CONFIG:-${SCRIPT_DIR}/mcp_llm_test/models_config.yaml}"
OUTPUT_DIR="${OUTPUT_DIR:-${SCRIPT_DIR}/test_results}"
CONCURRENCY="${CONCURRENCY:-1}"
TIMEOUT="${TIMEOUT:-600}"
RESUME="${RESUME:-false}"
ANALYZE="${ANALYZE:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*"
}

# Check if required files exist
check_prerequisites() {
    log_info "Checking prerequisites..."

    if [ ! -f "${MODELS_CONFIG}" ]; then
        log_error "Models config file not found: ${MODELS_CONFIG}"
        exit 1
    fi

    if [ ! -f "${SCRIPT_DIR}/mcp_llm_test/get_model_configs.py" ]; then
        log_error "Helper script not found: ${SCRIPT_DIR}/mcp_llm_test/get_model_configs.py"
        exit 1
    fi

    if [ ! -f "${SCRIPT_DIR}/mcp_llm_test/evaluate_mcp.py" ]; then
        log_error "Evaluation script not found: ${SCRIPT_DIR}/mcp_llm_test/evaluate_mcp.py"
        exit 1
    fi

    log_success "All prerequisites found"
}

# Create output directory
setup_output_dir() {
    log_info "Setting up output directory: ${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}"
    log_success "Output directory ready"
}

# Check if a model has completed results
is_model_complete() {
    local model_dir="$1"
    local marker_file="${model_dir}/.completed"

    [ -f "${marker_file}" ]
}

# Mark a model as completed
mark_model_complete() {
    local model_dir="$1"
    local marker_file="${model_dir}/.completed"

    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" > "${marker_file}"
}

# Run evaluation for a single model
run_model_evaluation() {
    local model_name="$1"
    local model_id="$2"
    local provider="$3"
    local api_key="$4"
    local api_base="$5"

    # Sanitize model_id for directory name (replace / with _)
    local model_dir_name="${model_id//\//_}"
    local model_dir="${OUTPUT_DIR}/${model_dir_name}"

    # Check if model is already completed (resume mode)
    if [ "${RESUME}" = "true" ] && is_model_complete "${model_dir}"; then
        log_info "Skipping ${model_name} (already completed)"
        return 0
    fi

    log_info "Testing model: ${model_name} (${model_id})"
    log_info "  Provider: ${provider}"
    log_info "  Output: ${model_dir}"

    # Create model output directory
    mkdir -p "${model_dir}"

    # Run evaluation
    local start_time=$(date +%s)
    local exit_code=0

    python "${SCRIPT_DIR}/mcp_llm_test/evaluate_mcp.py" \
        --provider "${provider}" \
        --model "${model_id}" \
        --output-dir "${model_dir}" \
        --concurrency "${CONCURRENCY}" \
        --timeout "${TIMEOUT}"

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ ${exit_code} -eq 0 ]; then
        log_success "Completed ${model_name} in ${duration}s"
        mark_model_complete "${model_dir}"
    else
        log_error "Failed ${model_name} (exit code: ${exit_code})"
        echo "FAILED: exit code ${exit_code}" > "${model_dir}/.failed"
        return ${exit_code}
    fi
}

# Main execution
main() {
    echo "════════════════════════════════════════════════════════════════"
    echo "  Multi-Model Benchmark Testing"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    log_info "Configuration:"
    echo "  Models config: ${MODELS_CONFIG}"
    echo "  Output directory: ${OUTPUT_DIR}"
    echo "  Concurrency: ${CONCURRENCY}"
    echo "  Timeout: ${TIMEOUT}s"
    echo "  Resume mode: ${RESUME}"
    echo "  Auto-analyze: ${ANALYZE}"
    echo ""

    # Prerequisites
    check_prerequisites
    setup_output_dir

    # Get enabled models from configuration
    log_info "Loading model configurations..."
    local models_json
    models_json=$(python "${SCRIPT_DIR}/mcp_llm_test/get_model_configs.py" \
        --config "${MODELS_CONFIG}" \
        --format json)

    local model_count
    model_count=$(echo "${models_json}" | python -c "import sys, json; print(len(json.load(sys.stdin)))")

    if [ "${model_count}" -eq 0 ]; then
        log_warning "No enabled models found in configuration"
        exit 0
    fi

    log_success "Found ${model_count} enabled model(s)"
    echo ""

    # Process each model
    local failed_models=()
    local completed_models=()
    local skipped_models=()

    echo "${models_json}" | python -c "
import sys
import json
models = json.load(sys.stdin)
for model in models:
    print(f\"{model['name']}|{model['id']}|{model['provider']}|{model.get('api_key', '')}|{model.get('api_base', '')}\")
" | while IFS='|' read -r name id provider api_key api_base; do
        echo "────────────────────────────────────────────────────────────────"

        if run_model_evaluation "${name}" "${id}" "${provider}" "${api_key}" "${api_base}"; then
            completed_models+=("${name}")
        else
            failed_models+=("${name}")
        fi

        echo ""
    done

    # Summary
    echo "════════════════════════════════════════════════════════════════"
    echo "  Benchmark Summary"
    echo "════════════════════════════════════════════════════════════════"

    local total_completed=$(find "${OUTPUT_DIR}" -name ".completed" | wc -l | tr -d ' ')
    local total_failed=$(find "${OUTPUT_DIR}" -name ".failed" | wc -l | tr -d ' ')
    local total_models=$((total_completed + total_failed))

    log_info "Total models processed: ${total_models}"
    log_success "Completed: ${total_completed}"

    if [ "${total_failed}" -gt 0 ]; then
        log_error "Failed: ${total_failed}"
    fi

    echo ""

    # Generate analysis
    if [ "${ANALYZE}" = "true" ] && [ "${total_completed}" -gt 0 ]; then
        log_info "Generating aggregated results..."

        if [ -f "${SCRIPT_DIR}/mcp_llm_test/analyze_results.py" ]; then
            python "${SCRIPT_DIR}/mcp_llm_test/analyze_results.py" "${OUTPUT_DIR}" || {
                log_warning "Analysis script failed, but results are available in ${OUTPUT_DIR}"
            }
        else
            log_warning "Analysis script not found (${SCRIPT_DIR}/mcp_llm_test/analyze_results.py)"
            log_info "Results are available in: ${OUTPUT_DIR}"
        fi
    else
        log_info "Results are available in: ${OUTPUT_DIR}"
    fi

    echo ""
    log_success "Benchmark complete!"

    # Exit with error if any models failed
    if [ "${total_failed}" -gt 0 ]; then
        exit 1
    fi
}

# Run main function
main "$@"
