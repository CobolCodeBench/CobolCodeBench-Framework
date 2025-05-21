import os
import sys
import pandas as pd
from loguru import logger
import json
from fuzzywuzzy import fuzz
from src.utils import Model, execute_command
import difflib


class CompileExecute:
    def __init__(self, model: Model, csv_path, mode="instruct"):
        self.model = model.name
        self.csv_path = csv_path
        self.mode = mode.lower()  # "instruct" or "complete"
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # Structure output path based on mode
        if self.mode == "instruct":
            self.output_path = f"{self.current_dir}/preds/{model.name}/instruct"
        else:
            self.output_path = f"{self.current_dir}/preds/{model.name}/complete"

        os.makedirs(self.output_path, exist_ok=True)

        try:
            # Load appropriate JSON file based on mode
            if self.mode == "instruct":
                json_file_path = './data/Instruction_Set.json'
            else:
                json_file_path = './data/Completion_Set.json'

            with open(json_file_path, 'r') as file:
                self.instruction_set = json.load(file)
            logger.info(f"Loaded {json_file_path} successfully")

        except Exception as e:
            logger.error(f"Error occurred while reading JSON file: {e}")

        try:
            self.df = pd.read_csv(csv_path)
            logger.info(f"Data frame read successfully")

        except Exception as e:
            logger.error(f"Error occurred while reading csv file {e}")
        self.total = 0
        self.compiled = 0
        self.executed = 0

    def create_input_files(self, program_name):
        """
        Create input files for the given program name.
        Args:
            program_name (str): The name of the program for which to create input files.
        Returns:
            bool: True if input files were created successfully, False otherwise.
        """
        try:
            res = next((item for item in self.instruction_set if item['Program_name'] == program_name), None)
            input_file_names = res['input_file_names']

            if isinstance(input_file_names, list) and input_file_names != "":
                for input_file in input_file_names:
                    input_file_path = os.path.join(self.output_path, program_name, input_file)
                    print("*Input File Path:",input_file_path,end="")
                    with open(input_file_path, "w+") as f:
                        f.write(res['inputs'][input_file])


            elif isinstance(input_file_names, str) and input_file_names != "":
                input_file_path = os.path.join(self.output_path, program_name, input_file_names)
                print("*Input File Path:",input_file_path)
                with open(input_file_path, "w+") as f:
                    f.write(res['inputs'][input_file_names])

            return True

        except Exception as e:
            logger.error(f"error creating input files {e}")
            return False

    def code_similarity_score(self,code1, code2):
        """
        Calculate the similarity score between two code snippets.
        Returns a float between 0.0 and 1.0.
        """
        logger.info(code1[:10],"****",code2[:10])
        # Use difflib's SequenceMatcher to compare the two codes
        sequence_matcher = difflib.SequenceMatcher(None, code1, code2)

        # Get the similarity ratio (between 0.0 and 1.0)
        return sequence_matcher.ratio()

    def compare_results(self, program_name):
        """
        Compare the actual output of the program with the expected output.
        Args:
            program_name (str): The name of the program to compare.
        Returns:
            float: The similarity score between the actual and expected output.
        """
        try:
            res = next((item for item in self.instruction_set if item['Program_name'] == program_name), None)
            if not res:
                return 0.0

            output_file_names = res['output_file_names']
            similarity_scores = []
            if isinstance(output_file_names, list) and output_file_names:
                for output_file in output_file_names:
                    output_file_path = os.path.join(self.output_path, program_name, output_file)

                    # Return 0.0 if file doesn't exist
                    if not os.path.exists(output_file_path):
                        return 0.0

                    with open(output_file_path, "r") as f:
                        actual_output = f.read()

                    expected_output = res['outputs'].get(output_file, "")

                    # Calculate similarity score (0-100 as integer)
                    exact_match = 1.0 if actual_output == expected_output else 0.0
                    edit_distance = fuzz.ratio(actual_output, expected_output) / 100.0

                    # Average of EM and ED
                    score = (exact_match + edit_distance) / 2.0
                    similarity_scores.append(score)

            elif isinstance(output_file_names, str) and output_file_names:
                output_file_path = os.path.join(self.output_path, program_name, output_file_names)

                # Return 0.0 if file doesn't exist
                if not os.path.exists(output_file_path):
                    return 0.0

                with open(output_file_path, "r") as f:
                    actual_output = f.read()

                expected_output = res['outputs'].get(output_file_names, "")

                # Calculate similarity score
                exact_match = 1.0 if actual_output == expected_output else 0.0
                edit_distance = fuzz.ratio(actual_output, expected_output) / 100.0

                # Average of EM and ED
                score = (exact_match + edit_distance) / 2.0
                similarity_scores.append(score)

            # Return average score across all files if there are multiple,
            # or the single score if there's only one file
            return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0

        except Exception as e:
            logger.error(f"Error comparing results for {program_name}: {e}")
            return 0.0

    def compile(self):
        compiled_res = []
        executed = []
        result_match = []
        code_similarity_scores = []

        try:
            total_rows = len(self.df)
            logger.info(f"Processing {total_rows} programs")

            for index, row in self.df.iterrows():
                try:
                    program = str(row['Generated_program'])
                    expected_program = str(row['Expected_program'])
                    logger.info(f"Processing program {index+1}/{total_rows}: {row['Program_name']}")

                    # Initialize with 0 values in case of any errors
                    code_similarity = 0.0
                    compiled = 0
                    executed_flag = 0
                    result_score = 0.0

                    # Code similarity calculation
                    logger.info(f"Code Similarity score started")
                    try:
                        # Uncomment this to enable code similarity scoring
                        # code_similarity = self.code_similarity_score(program, expected_program)
                        # Round to 2 decimal places
                        code_similarity = 0.0  # Placeholder 
                    except Exception as e:
                        logger.error(f"Error calculating code similarity: {e}")

                    code_similarity_scores.append(round(code_similarity, 2))

                    # Compilation
                    logger.info(f"Compilation started")
                    if not program.startswith("       IDENTIFICATION DIVISION."):
                        program = "       " + program.lstrip()

                    program_name = f"{row['Program_name']}"
                    program_folder_path = os.path.join(self.output_path, program_name)

                    os.makedirs(program_folder_path, exist_ok=True)
                    program_path = os.path.join(program_folder_path, f"{program_name}.cbl")

                    with open(program_path, "w+") as f:
                        f.write(program)

                    logger.info(f"compiling {program_name}")

                    # change to program directory to execute
                    program_dir = os.path.join(self.output_path, program_name)
                    os.chdir(program_dir)

                    output_executable = os.path.join(program_dir, f'{program_name}')
                    # compile cmd
                    compile_cmd = f'cobc -x -o {output_executable} {program_path}'

                    try:
                        compile_result = execute_command(compile_cmd)

                        if compile_result.returncode == 0:
                            compiled = 1
                            self.compiled += 1
                            logger.success(f"{program_name} is successfully compiled")

                            # Create Input files
                            if self.create_input_files(program_name):
                                try:
                                    execute_cmd = f'./{program_name}'
                                    execute_result = execute_command(execute_cmd)
                                    if execute_result.returncode == 0:
                                        executed_flag = 1
                                        self.executed += 1
                                        logger.success(f"{program_name} is successfully executed")

                                        # Compare results
                                        result_score = self.compare_results(program_name)
                                    else:
                                        logger.error(f"Execution failed for {program_name}")
                                except Exception as e:
                                    logger.error(f"Execution error for {program_name}: {e}")
                            else:
                                logger.error(f"Error occurred while creating input files for {program_name}")
                        else:
                            logger.error(f"Compilation failed for {program_name}")
                    except Exception as e:
                        logger.error(f"Compilation error for {program_name}: {e}")

                    # Append results for this program
                    compiled_res.append(compiled)
                    executed.append(executed_flag)
                    result_match.append(round(result_score, 2))

                except Exception as e:
                    logger.error(f"Error processing program {row.get('Program_name', f'at index {index}')}: {e}")
                    # Ensure lists stay the same length by adding default values
                    if len(code_similarity_scores) < index + 1:
                        code_similarity_scores.append(0.0)
                    if len(compiled_res) < index + 1:
                        compiled_res.append(0)
                    if len(executed) < index + 1:
                        executed.append(0)
                    if len(result_match) < index + 1:
                        result_match.append(0.0)

            # Ensure all arrays are the same length
            list_length = len(self.df)
            compiled_res = compiled_res[:list_length] + [0] * (list_length - len(compiled_res))
            executed = executed[:list_length] + [0] * (list_length - len(executed))
            result_match = result_match[:list_length] + [0.0] * (list_length - len(result_match))
            code_similarity_scores = code_similarity_scores[:list_length] + [0.0] * (list_length - len(code_similarity_scores))

            # Create the final results DataFrame
            final_results = pd.DataFrame({
                'Program_name': self.df['Program_name'],
                'Cobol_Eval': self.df['Cobol_Eval'],
                'Generated_program': self.df['Generated_program'],
                'Expected_program': self.df['Expected_program'],
                'Bert_score': self.df['Bert_score'],
                'Code Similarity Score': code_similarity_scores,
                'Compiled': compiled_res,
                'Executed': executed,
                'Result_match': result_match
            })

            logger.success(f"Compilation completed")
            logger.info(f"Total programs compiled: {sum(compiled_res)} \nTotal programs executed: {sum(executed)} \nTotal results matched: {sum(result_match)}")

            # Save results
            try:
                # Get the directory of the current script
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # Navigate to the parent directory
                parent_dir = os.path.dirname(current_dir)
                # Change to the parent directory
                os.chdir(parent_dir)

                compile_results_dir = f"final_results/{self.mode}"
                if not os.path.exists(compile_results_dir):
                    os.makedirs(compile_results_dir, exist_ok=True)
                    logger.info("final_results directory created")

                logger.info(f"final_results directory path: {os.path.abspath(compile_results_dir)}")

                # When saving final results
                final_results_path = os.path.join(compile_results_dir, f"{self.model}_{self.mode}_final_results.csv")
                final_results.to_csv(final_results_path, index=False)
                logger.info(f"Results saved to {final_results_path}")
            except Exception as e:
                logger.error(f"Error saving results: {e}")

            return final_results

        except Exception as e:
            logger.error(f"Error occurred during compilation: {e}")
            # Try to create a basic results DataFrame with available data
            try:
                # Ensure all arrays have the same length
                list_length = len(self.df)
                compiled_res = compiled_res[:list_length] + [0] * (list_length - len(compiled_res))
                executed = executed[:list_length] + [0] * (list_length - len(executed))
                result_match = result_match[:list_length] + [0.0] * (list_length - len(result_match))
                code_similarity_scores = code_similarity_scores[:list_length] + [0.0] * (list_length - len(code_similarity_scores))

                final_results = pd.DataFrame({
                    'Program_name': self.df['Program_name'],
                    'Compiled': compiled_res,
                    'Executed': executed,
                    'Result_match': result_match
                })

                logger.error("Created partial results due to error")
                logger.info(final_results)
                return final_results
            except Exception as e:
                logger.error(f"Could not create results dataframe: {e}")
                return None

if __name__ == "__main__":
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate to the parent directory
    parent_dir = os.path.dirname(current_dir)
    # Change to the parent directory
    os.chdir(parent_dir)
    model_list = []
    # Open the text file and read each line
    with open('evaluation/model_list.txt', 'r') as file:
        for line in file:
            # Append each line to the model_list
            model_list.append(line.strip())

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(parent_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Process both instruct and complete modes
    modes = ["instruct", "complete"]

    for model_name in model_list:
        for mode in modes:
            # Configure logger to write to a file for this specific model and mode
            log_file_path = os.path.join(logs_dir, f"{model_name}_{mode}.txt")

            # Remove any existing handlers
            logger.remove()
            # Add a new handler that writes to the model-specific log file
            logger.add(log_file_path, rotation="10 MB", level="INFO")
            logger.info(f"Starting processing for model: {model_name}, mode: {mode}")

            model = Model(name=model_name)
            path = os.path.join("./evaluation_results", mode, f"{model.name}_evaluation_results.csv")
            if os.path.exists(path):
                # Redirect stdout to a file
                stdout_log_path = os.path.join(logs_dir, f"{model_name}_{mode}_stdout.txt")
                with open(stdout_log_path, 'w') as stdout_file:
                    # Store original stdout
                    original_stdout = sys.stdout
                    sys.stdout = stdout_file

                    try:
                        print(f"Starting compilation for model: {model_name}, mode: {mode}")
                        runner = CompileExecute(model, path, mode=mode)
                        results = runner.compile()
                        print(f"Finished processing model: {model_name}, mode: {mode}")
                        if results is not None:
                            print(f"Results summary: {len(results)} programs processed")
                            print(f"Compiled: {sum(results['Compiled'])} - Executed: {sum(results['Executed'])} - Match: {sum(results['Result_match'])}")
                    finally:
                        # Restore original stdout
                        sys.stdout = original_stdout

                # Merge stdout and logger outputs
                with open(log_file_path, 'a') as log_file, open(stdout_log_path, 'r') as stdout_file:
                    log_file.write("\n\n--- STDOUT OUTPUT ---\n\n")
                    log_file.write(stdout_file.read())

                # Remove the separate stdout file
                os.remove(stdout_log_path)

                logger.success(f"Completed processing model: {model_name}, mode: {mode}")
                logger.info(f"All logs saved to {log_file_path}")
            else:
                logger.error(f"CSV file not found: {path}")
                logger.info(f"Current directory {os.getcwd()}, Result directory: {path}")
