from loguru import logger
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from src.utils import extract_code_block, Model
from .llm_generator import LLMGenerator

#@memory.cache
def hf_instruct(prompt, model, tokenizer, max_length=8000, eos_token=None) -> str:
    """
    Generate text using a Hugging Face model with instruction-based prompting.
    Args:
        prompt (str): The input prompt for the model.
        model: The Hugging Face model to use for generation.
        tokenizer: The tokenizer for the model.
        max_length (int): Maximum length of the generated text.
        eos_token (str): End-of-sequence token for the model.
    Returns:
        str: The generated text.
    """
    inputs = tokenizer.encode(prompt, return_tensors="pt", add_special_tokens=True)
    outputs = model.generate(inputs, max_new_tokens=max_length, use_cache=True, do_sample=False, repetition_penalty=1.1)
    text_output = tokenizer.decode(outputs[0], skip_special_tokens=False)[len(prompt):]
    try:
      eos_token = tokenizer.eos_token if eos_token is None else eos_token
      if eos_token and text_output.endswith(eos_token):
          text_output = text_output[: -len(eos_token)]
      if text_output.startswith(tokenizer.bos_token):
          text_output = text_output[len(tokenizer.bos_token):]
    finally:
      if eos_token in text_output:
         text_output = text_output.split(eos_token)[0]
    return text_output

class HuggingfaceInstruct(LLMGenerator):
    """
    Completes WORKING-STORAGE then PROCEDURE DIVISION with local Huggingface model
    """
    def __init__(self, model: Model, prompt_type):
        super().__init__(model, prompt_type)
        self.hf_model = AutoModelForCausalLM.from_pretrained(model.name, device_map="auto", torch_dtype=torch.bfloat16)
        if model.tokenizer:
            self.hf_tokenizer = AutoTokenizer.from_pretrained(model.tokenizer)
        else:
            self.hf_tokenizer = AutoTokenizer.from_pretrained(model.name)

    def solve(self, eval, sample_id=0):
        logger.info(f"generating {eval['Program_name']}")
        sol = hf_instruct(eval["Cobol_Eval"], self.hf_model, self.hf_tokenizer, 8000, eos_token=self.hf_tokenizer.eos_token)
        logger.info(sol)
        program = extract_code_block(sol)
        return program