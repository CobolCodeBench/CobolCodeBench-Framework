# COBOL Code Bench

<img src="https://cdn-uploads.huggingface.co/production/uploads/64b934072f796fffbb0ce278/OcyCB82hpMun9m3G0hpVK.png">


This framework serves as a comprehensive evaluation platform for assessing the code generation and completion capabilities of various Large Language Models (LLMs) specifically within the COBOL programming language.

## Objective:

To rigorously measure the performance of state-of-the-art AI models in generating valid, functional, and efficient COBOL code based on the prompts and specifications provided by the [CobolCodeBench](https://huggingface.co/datasets/harshini-kumar/CobolCodeBench) benchmark.

## Project Structure

```
cobol-code-generator
├── src
│   ├── generator
│   │   ├── __init__.py
│   │   ├── llm_generator.py
│   │   ├── openai_chat.py
│   │   ├── huggingface_instruct.py
│   │   ├── huggingface_complete.py
│   │   └── huggingface_api.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── code_extractor.py
│   │   ├── file_utils.py
│   │   └── command_utils.py
│   ├── evaluator
│   │   ├── __init__.py
│   │   |── compile_execute.py
|   |   |── evaluate.py
|   |   └── score_evaluator.py
|   ├── logs
|   ├── log-parser
|       ├── output
|       ├── structure_logs
|       ├── log_utils.py
|       ├── log_summary.py
|       └── README.md
│   ├── data
│   │   └── data_procesor.py
│   ├── Instruction_Set.json
│   └── Completion_Set.json
│   └── __init__.py
├── config
│   └── model_config.py
├── main.py
├── requirements.txt
└── README.md
```

## Features

- **Model Integration**: Supports multiple modes for loading models for code generation like API and Hugging Face.
- **Evaluation**: Provides tools to evaluate the generated code against expected outputs.
- **Data Handling**: Includes utilities for loading and processing instruction and completion sets from JSON files.
- **Command Execution**: Utilities for executing shell commands related to COBOL code compilation.

## Installation

To install the required dependencies, run:
```
pip install -r requirements.txt
```

## Usage

To run the code generator, execute the following command:

```
python main.py
```

Make sure to configure the model settings in `config/model_config.py` as needed.

## Generation only
```
python main.py --model gpt-4o --mode Instruct --method chat-api --generation-only
```

## Run evaluation after generation is complete
```
python evaluate.py
```

## Or run specific evaluation types
```
python evaluate.py --bert-score
python evaluate.py --compile-execute
```

## Or specify a different model/mode than the last run
```
python evaluate.py --model claude-sonnet --mode Complete
```
## Setting .env for API keys
```
[ "GPT":{
        "API_KEY": "your_openai_api_key",
        "MODEL": "gpt-3.5-turbo",
        "ENDPOINT": "https://api.openai.com/v1/chat/completions",
        "TEMPERATURE": 0.7,
        "MAX_TOKENS": 150,
        "TOP_P": 1.0,
        "FREQUENCY_PENALTY": 0.0,
        "PRESENCE_PENALTY": 0.0
    },
    "GEMINI":{
        "API_KEY": "your_gemini_api_key",
        "MODEL": "gemini-1.5-flash",
        "ENDPOINT":"",
        "TEMPERATURE": 0.7,
        "MAX_TOKENS": 150,
        "TOP_P": 1.0,
        "FREQUENCY_PENALTY": 0.0,
        "PRESENCE_PENALTY": 0.0
    },
    "CLAUDE":{
        "API_KEY": "your_claude_api_key",
        "MODEL": "claude-3-5-sonnet",
        "ENDPOINT":"",
        "TEMPERATURE": 0.7,
        "MAX_TOKENS": 150,
        "TOP_P": 1.0,
        "FREQUENCY_PENALTY": 0.0,
        "PRESENCE_PENALTY": 0.0
    }]
```

⚠️ **Warning: Repository Migration and Refactoring in Progress** ⚠️

Please be aware that this repository has recently been migrated and is undergoing significant refactoring from a private enterprise environment to a public repository.

**As a result, you may experience unstable performance, unexpected behavior, and incomplete features.**

We are actively working to stabilize the codebase and improve its functionality in this new public setting.


### Current Progress & To-Do:

Here's a high-level overview of the ongoing work. You can check back here for updates on our progress:

* [x] ~~Core codebase migration complete~~
* [ ] Testing Initial model integration framework (huggingface, chat-api)
* [ ] Logs setup to capture compilation and execution logs seperately & Scores seperately
* [ ] Generator features stabilized
* [ ] Evaluator features stabilized
* [ ] Security review of API and input validation
* [ ] Comprehensive testing implemented
* [ ] Essential documentation updated
* [ ] Full documentation complete

**We appreciate your patience and understanding as we work to make this repository stable and reliable.**

If you encounter any issues, please feel free to report them as GitHub issues. However, please keep in mind that our immediate focus is on stabilizing the core functionality.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

