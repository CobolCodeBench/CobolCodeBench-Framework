from loguru import logger
import os
from transformers import AutoTokenizer
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import json
from src.utils import extract_code_block, Model
from . import LLMGenerator

def huggingface_api_inference(prompt, model):
    """
    Generate text using a Hugging Face API inferencing with instruction-based prompting.
    Args:
        prompt (str): The input prompt for the model.
        model: The Hugging Face model to use for generation.
        tokenizer: The tokenizer for the model.
        max_length (int): Maximum length of the generated text.
        eos_token (str): End-of-sequence token for the model.
    Returns:
        str: The generated text.
    """
    # Initialize the InferenceClient with your Hugging Face API key
    load_dotenv()

    # Get API key from environment variables
    provider = os.getenv("HUGGINGFACE_API_PROVIDER",default="nebius")
    api_key = os.getenv("HUGGINGFACE_API_KEY",default=None)
    try:
        if api_key is None:
            logger.error("HUGGINGFACE_API not found in environment variables")
            raise ValueError("API key is missing. Please set HUGGINGFACE_API in your .env file")

        client = InferenceClient(
            provider=provider,
            api_key=api_key,
        )
        messages = [
            {
                "role": "user",
                "content": prompt},
        ]

        output = client.chat.completions.create(
            model=model.name,
            messages=messages,
            temperature=0,
            max_tokens=8000,
            top_p=0.95,
        )
        return output.choices[0].message.content
    except Exception as e:
        logger.error(f"Error during Hugging Face API inference: {e}")
        return ""

class HuggingfaceAPIInferenceGenerator(LLMGenerator):
    """
    Completes WORKING-STORAGE then PROCEDURE DIVISION with Hugging Face's API.
    """

    def __init__(self, model: Model, prompt_type):
        super().__init__(model, prompt_type)
        self.hf_model = model
        self.hf_tokenizer = model.tokenizer
        self.prompt_type = prompt_type
        if model.tokenizer:
            self.hf_model.tokenizer = AutoTokenizer.from_pretrained(model.tokenizer)
        else:
            self.hf_model.tokenizer = AutoTokenizer.from_pretrained(model.name)

    def solve(self, eval, sample_id=0):
        logger.info(f"Generating {eval['Program_name']}")
        sol = huggingface_api_inference(eval["Cobol_Eval"], self.hf_model)
        if self.prompt_type == "Complete":
            program = self.combine_prompt_and_solution(eval["Cobol_Eval"], sol)
        else:
            program = extract_code_block(sol)
        logger.info(program)
        return program

    def combine_prompt_and_solution(self, prompt, solution):
        """
        Construct the final program by combining the prompt and solution.
        Args:
            prompt (str): The input prompt for the model.
            sol (str): The generated solution from the model.
        Returns:
            str: The final program.
        """
        combined_program = f"{prompt}\n{solution}"
        return combined_program