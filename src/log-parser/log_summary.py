import os
import json
from collections import defaultdict, Counter
import argparse
import re


def load_structured_logs(log_dir):
    logs = []
    for filename in os.listdir(log_dir):
        if filename.endswith("_structured.json"):
            model, mode = parse_model_mode(filename)
            with open(os.path.join(log_dir, filename), "r") as f:
                try:
                    data = json.load(f)
                    for entry in data:
                        entry["_model"] = model
                        entry["_mode"] = mode
                    logs.extend(data)
                except json.JSONDecodeError:
                    print(f"Warning: Couldn't parse {filename}")
    return logs


def parse_model_mode(filename):
    # Example: claude-3-sonnet_instruct_structured.json
    base = filename.replace("_structured.json", "")
    match = re.match(r"(.+?)_(instruct|complete)$", base)
    if match:
        return match.group(1), match.group(2)
    return base, "unknown"


def summarize_logs(logs):
    summary = {
        "groups": defaultdict(lambda: {
            "success": 0,
            "failure": 0,
            "success_tasks": [],
            "failure_tasks": [],
            "compile_errors": Counter()
        })
    }
    for entry in logs:
        key = (entry["_model"], entry["_mode"])
        group = summary["groups"][key]

        task_id = entry.get("task_id", "unknown_task")
        if entry.get("compilation_success"):
            group["success"] += 1
            group["success_tasks"].append(task_id)
        else:
            group["failure"] += 1
            group["failure_tasks"].append(task_id)
            for err in entry.get("compile_error_log", []):
                msg = err.get("message", "").lower().strip()
                if msg:
                    group["compile_errors"][msg] += 1

    return summary


def render_markdown(summary):
    md = [""]

    md.append("## Compilation Summary per Model & Mode\n")
    for (model, mode), stats in summary["groups"].items():
        md.append(f"### Model: `{model}` | Mode: `{mode}`")
        md.append(f"- ✅ Successes: {stats['success']}")
        md.append(f"- ❌ Failures: {stats['failure']}")

        if stats["success_tasks"]:
            md.append("\n**Successful task functions:**")
            md.append(f" {', '.join(stats['success_tasks'])}")

        if stats["failure_tasks"]:
            md.append("\n**Failed task functions:**")
            md.append(f" {', '.join(stats['failure_tasks'])}")
        if stats["compile_errors"]:
            md.append("\n## Top Compile Errors:")
            md.append("| Error Message | Count |")
            md.append("|---------------|-------|")
            for msg, count in stats["compile_errors"].most_common(5):
                md.append(f"| {msg} | {count} |")

        md.append("")  # spacing

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_dir", default="structured_logs", help="Directory with structured logs")
    parser.add_argument("--format", choices=["markdown"], default="markdown", help="Output format")
    parser.add_argument("--output", help="File to write output (optional)")
    args = parser.parse_args()

    logs = load_structured_logs(args.log_dir)
    summary = summarize_logs(logs)

    if args.format == "markdown":
        report = render_markdown(summary)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Summary written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
