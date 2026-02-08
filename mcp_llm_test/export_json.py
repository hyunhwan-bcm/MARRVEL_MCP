"""
Pickle-to-JSON converter and JSON-to-HTML viewer for MARRVEL-MCP evaluation results.

Converts cached pickle evaluation results into portable JSON, and can also
generate HTML reports from exported JSON files.

Usage:
    # Export pickle cache to JSON
    python mcp_llm_test/export_json.py <run_id> [options]

    # Generate HTML report from JSON and open in browser
    python mcp_llm_test/export_json.py --view <json_file>

Options:
    --output, -o PATH    Output file (default: <run_dir>/results.json)
    --pretty             Pretty-print JSON (default: minified)
    --compact            Strip verbose LangChain internal fields from serialized_messages
    --list-runs          List available run IDs and exit
    --view JSON_FILE     Generate HTML report from exported JSON and open in browser
"""

import argparse
import json
import pickle
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow running as standalone script or as import from evaluate_mcp.py
try:
    from evaluation_modules.cache import CACHE_DIR
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from evaluation_modules.cache import CACHE_DIR

# LangChain internal fields to strip in --compact mode
_COMPACT_STRIP_KEYS = frozenset(
    {
        "model_config",
        "model_fields",
        "model_computed_fields",
        "model_extra",
        "lc_attributes",
        "lc_secrets",
    }
)


def _strip_internal_keys(obj: Any) -> Any:
    """Recursively remove verbose LangChain internal fields from dicts/lists."""
    if isinstance(obj, dict):
        return {k: _strip_internal_keys(v) for k, v in obj.items() if k not in _COMPACT_STRIP_KEYS}
    if isinstance(obj, list):
        return [_strip_internal_keys(item) for item in obj]
    return obj


def _is_correct(classification: str) -> bool:
    """Check if a classification indicates a correct answer (same logic as reporting.py)."""
    return bool(re.search(r"\byes\b", classification.lower()))


def _parse_mode_from_filename(filename: str) -> tuple[str, str]:
    """Extract UUID and mode from a pickle filename.

    Follows the naming convention from cache.py:get_cache_path():
      {uuid}.pkl            -> tool mode
      {uuid}_vanilla.pkl    -> vanilla mode
      {uuid}_web.pkl        -> web mode
      {uuid}_{model_id}_{mode}.pkl -> multi-model (not yet supported)

    Returns:
        (uuid, mode) tuple
    """
    stem = Path(filename).stem  # strip .pkl

    if stem.endswith("_vanilla"):
        return stem[: -len("_vanilla")], "vanilla"
    if stem.endswith("_web"):
        return stem[: -len("_web")], "web"

    # Check for multi-model pattern: uuid_modelid_mode
    # Mode suffixes are always one of: _vanilla, _web, or none (tool)
    # If it doesn't end with _vanilla or _web, it's either:
    #   - plain uuid (tool mode)
    #   - uuid_modelid (tool mode with model prefix)
    # We treat the first 8 chars as UUID for basic cases
    return stem, "tool"


def list_runs() -> List[Dict[str, Any]]:
    """List all available run IDs with basic info."""
    runs = []
    if not CACHE_DIR.exists():
        return runs

    for run_dir in sorted(CACHE_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        pkl_files = list(run_dir.glob("*.pkl"))
        has_snapshot = (run_dir / "test_cases.yaml").exists()
        runs.append(
            {
                "run_id": run_dir.name,
                "num_results": len(pkl_files),
                "has_test_cases": has_snapshot,
                "modified": datetime.fromtimestamp(run_dir.stat().st_mtime).isoformat(),
            }
        )
    return runs


def build_export_json(
    run_id: str,
    compact: bool = False,
    run_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the consolidated JSON export from cached pickle results.

    Args:
        run_id: The run identifier (directory name under CACHE_DIR)
        compact: If True, strip verbose LangChain internal fields
        run_metadata: Optional dict of run-level metadata (model, provider, etc.)
            When called from evaluate_mcp.py, this is populated with the actual
            args used during evaluation. When converting old runs, metadata is
            extracted from pickle files on a best-effort basis.

    Returns:
        Dict containing the full export data ready for json.dumps()
    """
    run_dir = CACHE_DIR / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    # Load test_cases.yaml snapshot for metadata lookup
    snapshot_path = run_dir / "test_cases.yaml"
    uuid_metadata: Dict[str, Dict[str, str]] = {}
    if snapshot_path.exists():
        import yaml

        with open(snapshot_path, "r", encoding="utf-8") as f:
            test_cases = yaml.safe_load(f) or []
        for idx, tc in enumerate(test_cases):
            tc_uuid = tc.get("uuid", "")
            case = tc.get("case", {})
            uuid_metadata[tc_uuid] = {
                "index": idx,
                "name": case.get("name", "Unknown"),
                "category": case.get("category", "Unknown"),
                "input": case.get("input", ""),
                "expected": case.get("expected", ""),
            }
    else:
        print(
            f"Warning: test_cases.yaml not found in {run_dir}, metadata will be limited",
            file=sys.stderr,
        )

    # Load all pickle files and group by UUID
    results_by_uuid: Dict[str, Dict[str, Dict[str, Any]]] = {}
    load_errors = []

    for pkl_path in sorted(run_dir.glob("*.pkl")):
        try:
            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
        except Exception as e:
            load_errors.append(f"{pkl_path.name}: {e}")
            continue

        uuid_part, mode = _parse_mode_from_filename(pkl_path.name)

        if uuid_part not in results_by_uuid:
            results_by_uuid[uuid_part] = {}
        results_by_uuid[uuid_part][mode] = data

    if load_errors:
        print(f"Warning: Failed to load {len(load_errors)} pickle file(s):", file=sys.stderr)
        for err in load_errors:
            print(f"  {err}", file=sys.stderr)

    # Build test_results list
    test_results = []
    # Summary counters per mode
    summary: Dict[str, Dict[str, int]] = {}

    for uuid_key, modes_data in results_by_uuid.items():
        meta = uuid_metadata.get(uuid_key, {})

        entry: Dict[str, Any] = {
            "index": meta.get("index", -1),
            "uuid": uuid_key,
            "name": meta.get("name", "Unknown"),
            "category": meta.get("category", "Unknown"),
            "question": meta.get("input", "")
            or modes_data.get("tool", modes_data.get("vanilla", modes_data.get("web", {}))).get(
                "question", ""
            ),
            "expected": meta.get("expected", "")
            or modes_data.get("tool", modes_data.get("vanilla", modes_data.get("web", {}))).get(
                "expected", ""
            ),
            "modes": {},
        }

        for mode_name, result_data in modes_data.items():
            classification = result_data.get("classification", "")
            correct = _is_correct(classification)

            # Update summary counters
            if mode_name not in summary:
                summary[mode_name] = {"passed": 0, "failed": 0, "error": 0}

            if result_data.get("status") == "error" or result_data.get("mode") == "error":
                summary[mode_name]["error"] += 1
            elif correct:
                summary[mode_name]["passed"] += 1
            else:
                summary[mode_name]["failed"] += 1

            mode_entry: Dict[str, Any] = {
                "response": result_data.get("response", ""),
                "classification": classification,
                "is_correct": correct,
                "tokens_used": result_data.get("tokens_used", 0),
                "input_tokens": result_data.get("input_tokens", 0),
                "output_tokens": result_data.get("output_tokens", 0),
                "tool_calls": result_data.get("tool_calls", []),
                "conversation": result_data.get("conversation", []),
            }

            # Include serialized_messages (may be large)
            serialized = result_data.get("serialized_messages", [])
            if compact and serialized:
                serialized = _strip_internal_keys(serialized)
            mode_entry["serialized_messages"] = serialized

            entry["modes"][mode_name] = mode_entry

        test_results.append(entry)

    # Sort by original index
    test_results.sort(key=lambda x: x["index"] if x["index"] >= 0 else float("inf"))

    # Compute rates
    for mode_name, counts in summary.items():
        total = counts["passed"] + counts["failed"] + counts["error"]
        counts["rate"] = round(counts["passed"] / total * 100, 1) if total > 0 else 0.0

    total_tests = len(test_results)

    # Build run-level metadata
    # Priority: 1) explicit run_metadata (from evaluate_mcp.py --export-json)
    #           2) run_config.yaml saved in the run directory
    #           3) best-effort extraction from pickle metadata fields
    effective_metadata: Dict[str, Any] = {}
    if run_metadata:
        effective_metadata = dict(run_metadata)
    else:
        # Try loading run_config.yaml first (saved by evaluate_mcp.py since this feature)
        run_config_path = run_dir / "run_config.yaml"
        if run_config_path.exists():
            import yaml

            with open(run_config_path, "r", encoding="utf-8") as f:
                run_config = yaml.safe_load(f) or {}
            effective_metadata = {
                "tested_model": run_config.get("tested_model", ""),
                "tested_provider": run_config.get("tested_provider", ""),
                "evaluator_model": run_config.get("evaluator_model", ""),
                "evaluator_provider": run_config.get("evaluator_provider", ""),
                "concurrency": run_config.get("concurrency"),
                "created_at": run_config.get("created_at", ""),
            }
            # Derive modes from config flags
            if run_config.get("with_web"):
                effective_metadata["modes"] = ["vanilla", "web", "tool"]
            elif run_config.get("with_vanilla"):
                effective_metadata["modes"] = ["vanilla", "tool"]
            else:
                effective_metadata["modes"] = sorted(summary.keys())
            if run_config.get("api_base"):
                effective_metadata["api_base"] = run_config["api_base"]
        else:
            # Fallback: extract model info from pickle metadata (best-effort)
            for modes_data in results_by_uuid.values():
                for result_data in modes_data.values():
                    meta = result_data.get("metadata", {})
                    if isinstance(meta, dict) and meta.get("model_used"):
                        effective_metadata.setdefault("tested_model", meta["model_used"])
                if "tested_model" in effective_metadata:
                    break
            effective_metadata["modes"] = sorted(summary.keys())

        # Add directory timestamp as run date if not already present
        if not effective_metadata.get("created_at"):
            try:
                effective_metadata["created_at"] = datetime.fromtimestamp(
                    run_dir.stat().st_mtime, tz=timezone.utc
                ).isoformat()
            except OSError:
                pass

    export = {
        "schema_version": "1.0",
        "run_id": run_id,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "run_metadata": effective_metadata,
        "total_tests": total_tests,
        "summary": summary,
        "test_results": test_results,
    }

    return export


def view_json_as_html(json_path: str) -> str:
    """Generate an HTML report from an exported JSON file and open it in the browser.

    Converts the JSON export format back into the structure expected by
    generate_html_report(), then delegates to the existing Jinja2 template.

    Args:
        json_path: Path to the exported JSON file

    Returns:
        Path to the generated HTML file
    """
    # Ensure project root is on path so reporting.py can import marrvel_mcp
    project_root = str(Path(__file__).parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from evaluation_modules.reporting import generate_html_report, open_in_browser

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_results = data.get("test_results", [])
    meta = data.get("run_metadata", {})
    modes = sorted(set().union(*(r["modes"].keys() for r in test_results))) if test_results else []

    # Determine report mode
    has_tool = "tool" in modes
    has_vanilla = "vanilla" in modes
    has_web = "web" in modes
    tri_mode = has_tool and has_vanilla and has_web
    dual_mode = has_tool and has_vanilla and not has_web

    # Convert JSON export format → generate_html_report() format
    _empty_mode = {
        "response": "",
        "classification": "N/A - no data",
        "tokens_used": 0,
        "tool_calls": [],
        "conversation": [],
        "serialized_messages": [],
    }

    def _get_mode(r: Dict, mode_name: str) -> Dict[str, Any]:
        md = r["modes"].get(mode_name, {})
        if not md or "classification" not in md:
            return dict(_empty_mode)
        return md

    results = []
    for r in test_results:
        entry: Dict[str, Any] = {
            "question": r["question"],
            "expected": r["expected"],
        }

        if tri_mode:
            for mode in ("vanilla", "web", "tool"):
                entry[mode] = _get_mode(r, mode)
        elif dual_mode:
            for mode in ("vanilla", "tool"):
                entry[mode] = _get_mode(r, mode)
        else:
            # Single mode — flatten the first (and only) mode into the top level
            single_mode = modes[0] if modes else "tool"
            md = _get_mode(r, single_mode)
            entry.update(
                {
                    "response": md.get("response", ""),
                    "classification": md.get("classification", ""),
                    "tokens_used": md.get("tokens_used", 0),
                    "tool_calls": md.get("tool_calls", []),
                    "conversation": md.get("conversation", []),
                    "serialized_messages": md.get("serialized_messages", []),
                }
            )

        results.append(entry)

    # Extract model info for header
    tested_model = meta.get("tested_model") or meta.get("model")
    tested_provider = meta.get("tested_provider") or meta.get("provider")
    evaluator_model = meta.get("evaluator_model")
    evaluator_provider = meta.get("evaluator_provider")

    html_path = generate_html_report(
        results,
        dual_mode=dual_mode,
        tri_mode=tri_mode,
        evaluator_model=evaluator_model,
        evaluator_provider=evaluator_provider,
        tested_model=tested_model,
        tested_provider=tested_provider,
    )

    open_in_browser(html_path)
    print(f"HTML report opened: {html_path}")
    return html_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert MARRVEL-MCP evaluation pickle caches to portable JSON, or view JSON as HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available runs
  python mcp_llm_test/export_json.py --list-runs

  # Export a run to JSON
  python mcp_llm_test/export_json.py 02c5809d --pretty

  # Export to a specific file
  python mcp_llm_test/export_json.py 02c5809d -o results.json --compact

  # View a JSON export as HTML report in browser
  python mcp_llm_test/export_json.py --view results.json
        """,
    )
    parser.add_argument(
        "run_id",
        nargs="?",
        help="Run ID to export (directory name under cache)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        metavar="PATH",
        help="Output file path (default: <run_dir>/results.json)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Strip verbose LangChain internal fields from serialized_messages",
    )
    parser.add_argument(
        "--list-runs",
        action="store_true",
        help="List available run IDs and exit",
    )
    parser.add_argument(
        "--view",
        type=str,
        metavar="JSON_FILE",
        help="Generate HTML report from an exported JSON file and open in browser",
    )

    args = parser.parse_args()

    # --view mode: JSON → HTML
    if args.view:
        json_file = Path(args.view)
        if not json_file.exists():
            print(f"Error: JSON file not found: {json_file}", file=sys.stderr)
            sys.exit(1)
        view_json_as_html(str(json_file))
        return

    if args.list_runs:
        runs = list_runs()
        if not runs:
            print("No evaluation runs found.")
            return
        print(f"{'Run ID':<12} {'Results':<10} {'Snapshot':<10} {'Modified'}")
        print("-" * 60)
        for r in runs:
            snapshot = "yes" if r["has_test_cases"] else "no"
            print(f"{r['run_id']:<12} {r['num_results']:<10} {snapshot:<10} {r['modified']}")
        return

    if not args.run_id:
        parser.error("run_id is required (use --list-runs to see available runs)")

    try:
        export_data = build_export_json(
            run_id=args.run_id,
            compact=args.compact,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = CACHE_DIR / args.run_id / "results.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    indent = 2 if args.pretty else None
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=indent, default=str, ensure_ascii=False)

    total = export_data["total_tests"]
    modes = ", ".join(
        f"{m}: {s['passed']}/{s['passed']+s['failed']+s['error']}"
        for m, s in export_data["summary"].items()
    )
    print(f"Exported {total} test results ({modes}) to {output_path}")


if __name__ == "__main__":
    main()
