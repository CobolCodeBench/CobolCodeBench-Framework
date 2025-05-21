import os
import re
import json
from typing import List, Dict

def remove_duplicate_compile_errors_nested(data):
    """
    Removes duplicate compiler error dictionaries from the 'compile_error_log'
    list within a list of data items.  

    Args:
        data: A list of dictionaries.  Each dictionary is expected to have a
            'compile_error_log' key whose value is a list of dictionaries.

    Returns:
        A new list with duplicate compiler error dictionaries removed from the
        'compile_error_log' lists. 
    """
    if not isinstance(data, list):
        return []
    original_data = new_data = 0
    for item in data:
        if isinstance(item, dict) and "compile_error_log" in item:
            error_list = item["compile_error_log"]
            original_data += len(error_list)
            if isinstance(error_list, list):
                unique_errors = []
                seen_errors = set()
                for error_dict in error_list:
                    # Convert the dictionary to a hashable tuple
                    error_tuple = (
                        error_dict["file"],
                        error_dict["line"],
                        error_dict["level"],
                        error_dict["message"],
                    )
                    if error_tuple not in seen_errors:
                        seen_errors.add(error_tuple)
                        unique_errors.append(error_dict)
                new_data += len(unique_errors)
                item["compile_error_log"] = unique_errors 
    print("Original Data:",original_data,"New Data:",new_data)            
    return data 

def parse_compilation_log(log_file_path: str) -> List[Dict]:
    task_logs = []
    current_task = None
    task_log = {}

    with open(log_file_path, "r") as f:
        lines = f.readlines()

    error_pattern = re.compile(r"(?P<file>.+\.cbl):(?P<line>\d+): (?P<level>error|warning|note): (?P<message>.+)", re.IGNORECASE)
    return_code_pattern = re.compile(r"Return code: (\d+)")
    task_start_pattern = re.compile(r"Processing program \d+/\d+: (?P<task_id>task_\w+)")
    success_pattern = re.compile(r"(?P<task_id>task_\w+) is successfully compiled")
    compile_fail_pattern = re.compile(r"Compilation failed for (?P<task_id>task_\w+)")

    for line in lines:
        line = line.strip()

        # Detect task start
        task_start_match = task_start_pattern.search(line)
        if task_start_match:
            if current_task and task_log:
                task_logs.append(task_log)  # Save previous task log if exists
            current_task = task_start_match.group("task_id")
            task_log = {
                "task_id": current_task,
                "compilation_success": None,
                "compile_error_log": [],
                "return_code": None,
                "timestamp": line.split("|")[0].strip(),
                "execution": {}  # Execution log will be added later
            }
            continue

        # Error message in compilation log
        err_match = error_pattern.search(line)
        if err_match and current_task:
            err_info = {
                "file": err_match.group("file"),
                "line": int(err_match.group("line")),
                "level": err_match.group("level").lower(),
                "message": err_match.group("message").strip()
            }
            task_log["compile_error_log"].append(err_info)

        # Return code in compilation log
        return_code_match = return_code_pattern.search(line)
        if return_code_match and current_task:
            task_log["return_code"] = int(return_code_match.group(1))

        # Compilation success
        success_match = success_pattern.search(line)
        if success_match:
            success_task_id = success_match.group("task_id")
            if task_log.get("task_id") == success_task_id:
                task_log["compilation_success"] = True

        # Compilation failure
        fail_match = compile_fail_pattern.search(line)
        if fail_match:
            fail_task_id = fail_match.group("task_id")
            if task_log.get("task_id") == fail_task_id:
                task_log["compilation_success"] = False

    if task_log:  # Add the last task if exists
        task_logs.append(task_log)

    return task_logs


def parse_execution_log(log_file_path: str) -> List[Dict]:
    task_logs = []
    current_task = None
    task_log = {}

    with open(log_file_path, "r") as f:
        lines = f.readlines()

    execution_start_pattern = re.compile(r"Execution started")
    execution_success_pattern = re.compile(r"Execution succeeded|Program exited with code 0", re.IGNORECASE)
    execution_fail_pattern = re.compile(r"Execution failed|Program exited with non-zero code", re.IGNORECASE)
    return_code_pattern = re.compile(r"Return code: (\d+)")
    runtime_error_pattern = re.compile(r"(Err:|Runtime error:)(?P<message>.+)", re.IGNORECASE)

    for line in lines:
        line = line.strip()

        # Detect task start in execution log
        task_match = re.search(r"Processing program \d+/\d+: (?P<task_id>task_\w+)", line)
        if task_match:
            if current_task and task_log:
                task_logs.append(task_log)  # Save previous task log if exists
            current_task = task_match.group("task_id")
            task_log = {
                "task_id": current_task,
                "execution_success": None,
                "execution_log": [],
                "return_code": None,
                "timestamp": line.split("|")[0].strip()
            }
            continue

        if current_task:
            if execution_start_pattern.search(line):
                task_log["execution_log"].append({"event": "Execution started", "timestamp": line.split("|")[0].strip()})

            if execution_success_pattern.search(line):
                task_log["execution_success"] = True
                task_log["execution_log"].append({"event": "Execution succeeded", "timestamp": line.split("|")[0].strip()})

            if execution_fail_pattern.search(line):
                task_log["execution_success"] = False
                task_log["execution_log"].append({"event": "Execution failed", "timestamp": line.split("|")[0].strip()})

            return_match = return_code_pattern.search(line)
            if return_match:
                task_log["return_code"] = int(return_match.group(1))

            err_match = runtime_error_pattern.search(line)
            if err_match:
                task_log["execution_log"].append({
                    "event": "Runtime Error",
                    "message": err_match.group("message").strip(),
                    "timestamp": line.split("|")[0].strip()
                })

    if task_log:  # Add the last task if exists
        task_logs.append(task_log)

    return task_logs


def write_combined_log(structured_data: List[Dict], output_path: str):
    structured_data = remove_duplicate_compile_errors_nested(structured_data)
    with open(output_path, "w") as f:
        json.dump(structured_data, f, indent=2)


def process_all_logs(input_dir: str = "../logs", output_dir: str = "structured_logs"):
    os.makedirs(output_dir, exist_ok=True)

    # Process both compilation and execution logs
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            input_path = os.path.join(input_dir, filename)
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}_structured.json"
            output_path = os.path.join(output_dir, output_filename)

            print(f"Processing {filename}...")

            # Parse compilation log
            compilation_logs = parse_compilation_log(input_path)

            # Process each task and add the execution logs if compilation is successful
            structured_data = []
            for compilation_log in compilation_logs:
                task_id = compilation_log["task_id"]
                if compilation_log.get("compilation_success"):  # Only proceed with execution log if compilation is successful
                    execution_logs = parse_execution_log(input_path)
                    for exec_log in execution_logs:
                        if exec_log["task_id"] == task_id:
                            compilation_log["execution"] = exec_log
                            break

                structured_data.append(compilation_log)

            write_combined_log(structured_data, output_path)
            print(f" → Combined structured log written to {output_path}")


if __name__ == "__main__":
    process_all_logs()
