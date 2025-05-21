# COBOLCodeBench – Log Parser

It supports structured logging, error categorization, and compilation/execution diagnostics across multiple model outputs and modes (e.g., instruct, complete).


##  Logs Structure
```
.
├── logs/                              # Raw compilation & execution logs(.txt)
├── log-parser/
    ├── structure_logs/                # Structured JSON logs after parsing
    ├── combined_log_utils.py      # Parses and structures all log files
    ├── log_summary.py             # Generates Markdown summaries
    └── README.md                      # This file
```


##  Pipeline Overview

### 1\. Collect Raw Logs

Each COBOL generation task (`task_func_XX`) is compiled and executed. Compilation and runtime logs are stored as plain `.txt` files under `logs/`.

### 2\. Parse & Structure Logs

Use the provided `log_utils.py` script to convert raw `.txt` logs into structured JSON logs:

```bash
python combined_log_utils.py
```

This script extracts and categorizes:

  * Compilation success/failure
  * Compilation error types & messages
  * Runtime/IO issues

It outputs one structured JSON file per model/mode in `structure_logs/`.

**Example output file:** `structure_logs/claude-3-5-sonnet_instruct_structured.json`

Each JSON object represents a single `task_func` log with fields like:

```json
{
  "task_id": "task_func_01",
  "compilation_success": false,
  "compile_error_log": [...],
  "execution_success": null,
  "execution_error_log": [...]
}
```

### 📊 Generate Summary Reports

To produce a human-readable summary of the results:

```bash
python log_summary.py --format markdown
```

**Optional flags:**
  * `--output output/summary.md`: saves the report to a file

The summary includes:

  * Total compilations per model & mode
  * Failed compilations
  * Top N most common compiler error messages

-----

##  Naming Convention

Structured logs follow this format: `{model_name}_{mode}_structured.json`

**Examples:**

  * `claude-3-sonnet_instruct_structured.json`
  * `llama-3-complete_structured.json`

The mode can be `instruct` or `complete`.

-----
##  Example

After running `combined_log_utils.py` and `log_summary.py`, a Markdown summary will look like this:

### Model: claude-3-5-sonnet | Mode: instruct

  *  Successes: 20
  *  Failures: 5
  *  Top Compile Errors:

| Error Message                 | Count |
| :---------------------------- | :---- |
| 'ws-idx' is not defined       | 3     |
| continuation character expected | 2   |

-----
