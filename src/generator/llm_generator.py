import json
import os
from loguru import logger
from src.utils import json_to_csv, Model, execute_command, cleanup_dylib
from src.evaluator.score_evaluator import ScoreEvaluator
import pandas as pd
class LLMGenerator:
    def __init__(self, model: Model, prompt_type):
        self.model = model
        self.prompt_type = prompt_type

        self.output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        f"preds/{model.name}")
        self.solutions_path = os.path.join(self.output_path, "solutions")
        self.errors_path = os.path.join(self.output_path, "errors")
        os.makedirs(self.solutions_path, exist_ok=True)
        os.makedirs(self.errors_path, exist_ok=True)

        if self.prompt_type == "Instruct":
          with open("Instruction_Set.json", "r") as f:
              self.evals = json.load(f)
        else:
          with open("Completion_Set.json", "r") as f:
              self.evals = json.load(f)

        self.total = 0
        self.compiled = 0
        self.samples = []

    def eval(self):
        """
        Generate code for each evaluation in the set and save the results.
        """
        for e in self.evals: #45 benchmark problems
            for k in range(self.model.samples_per_task): # samples=5
                try:
                    program = self.solve(e, k) #Fetch cobol code as response from the model for the prompt given and return
                    self.samples.append(
                        {"sample_id": k, "task_id": e["Program_name"], "completion": program}
                    )
                    logger.info('samples appended')
                    e["Generated_program"] = program

                    name = f"{e['Program_name']}"
                    path = os.path.join(self.solutions_path, f"{e['Program_name']}.cbl")
                    error_path = os.path.join(self.errors_path, f"{e['Program_name']}_errors.txt")


                    with open(path, "w+") as f:
                        f.write(program)
                        logger.info(f"program written successfully")

                    compiles = execute_command(f"cobc -fformat=variable {path}")

                    if compiles.returncode == 0:
                        self.compiled += 1
                        cleanup_dylib(name)
                    else:
                        errors = compiles.error

                        with  open(error_path,'w+') as file:
                            file.write(str(errors))
                            logger.info(f"errors written to a file successfully")
                    self.total += 1
                except Exception as e:
                    logger.error(e)

        try:
            with open(f"{self.output_path}/samples.jsonl", "w+") as f:
                for s in self.samples:
                    f.write(json.dumps(s) + "\n")
            json_path = f"preds/{self.model.name}_generated_results.jsonl"

            # Ensure the directory exists
            os.makedirs(os.path.dirname(json_path), exist_ok=True)

            # Open the file in write mode and write the evaluations
            with open(json_path, "w+") as f:
                for eval in self.evals:
                    f.write(json.dumps(eval) + "\n")
            try:
              GENERATION_PATH = json_to_csv(json_path,f"preds/{self.model.name}_generated_results.csv")
              if not os.path.exists(GENERATION_PATH):
                  logger.error(f"File not found: {GENERATION_PATH}")
                  exit(1)

              df = pd.read_csv(GENERATION_PATH)
              logger.info(f"Loaded {len(df)} records from {GENERATION_PATH}")

              golden_set = []
              for _, row in df.iterrows():
                  try:
                      golden_set.append({
                          "query": row['Cobol_Eval'],
                          "expected_response": row['Expected_Program']
                      })
                  except KeyError as e:
                      logger.warning(f"Missing key in row: {e}")

              # Make sure column names match what's expected in evaluate()
              instruction_set = df.rename(columns={
                  'program_name': 'Program_name',
                  'query': 'Cobol_Eval',
                  'generated_response': 'Generated_program',
                  'expected_response': 'Expected_Program'
              })

              logger.info("Starting evaluation...")
              scorer= ScoreEvaluator()
              scorer.evaluate(golden_set, instruction_set, self.model.name)
              logger.success("Evaluation completed successfully")
            except Exception as e:
              logger.error(f"Fatal error: {e}")
              import traceback
              logger.error(traceback.format_exc())
        except:
            logger.warning("Unable to create json or csv file")
        logger.info(f"Compiled {self.compiled} out of {self.total} programs")
        return True

    def solve(self, eval, sample_id=0):
        raise NotImplementedError
