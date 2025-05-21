import requests
from loguru import logger
from openai import AzureOpenAI
import json
import anthropic
import google.generativeai as genai  # New import for Gemini
from dotenv import load_dotenv
class ChatModelsGenerator:
    """
    A class that provides access to different chat models including GPT-4o, GPT-3.5, and Claude models.
    """

    def __init__(self):
        """Initialize the ChatModels class with proxy settings"""
        # self.proxies = {}

    def gemini(self, prompt, configs):
        """
        Queries a Gemini model with the given prompt.

        Args:
            prompt (str): The input prompt for the model
            configs (dict): Configuration containing API_KEY and model

        Returns:
            str: The generated response content
        """
        try:
            api_key = configs["API_KEY"]
            model = configs["model"]

            # Configure the Gemini API
            genai.configure(api_key=api_key)

            # Set up the model
            generation_config = {
                "temperature": 0.3,
                "max_output_tokens": 4096,
            }

            # Initialize the model
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config
            )

            # Set system instructions
            chat = model_instance.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": ["You are an AI assistant that generates GNU cobol code and return clean single markdown block."]
                    },
                    {
                        "role": "model",
                        "parts": ["I understand. I'll generate GNU COBOL code in a clean, single markdown code block format when you provide a request."]
                    }
                ]
            )

            # Generate the response
            response = chat.send_message(prompt)
            return response.text

        except Exception as e:
            raise SystemExit(f"Failed to make the request to Gemini. Error: {e}")

    def gpt(self, prompt, configs):
        """
        Queries the GPT-3.5 model with the given prompt.

        Args:
            prompt (str): The input prompt for the model
            configs (dict): Configuration containing API_KEY, ENDPOINT, and model

        Returns:
            str: The generated response content
        """
        API_KEY = configs["API_KEY"]
        ENDPOINT = configs["ENDPOINT"]
        API_VERSION = configs["api_version"]
        deployment = configs["model"]

        client = AzureOpenAI(
            azure_endpoint=ENDPOINT,
            api_key=API_KEY,
            api_version=API_VERSION,
        )
        messages= [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI assistant that generates cobol code and return clean code block. Output should consist of a single markdown code block following on from the lines above until the end of the program. It should terminate with `GOBACK`"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        try:
            completion = client.chat.completions.create(
                model=deployment,
                messages=messages,
                max_tokens=4096,
                temperature=0.3,
                stop=None,
                stream=False
            )
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")

        result = completion.to_json()
        result_json = json.loads(result)
        return result_json['choices'][0]['message']['content']

    def claude(self, query, configs, tokens=4096):
        """
        Queries a Claude model with the given prompt.
        
        Args:
            query (str): The input prompt for the model
            configs (dict): Configuration containing API_KEY and model
            tokens (int): Maximum number of tokens to generate
            
        Returns:
            str: The generated response content
        """
        try:
            api_key = configs["API_KEY"]
            model = configs["model"]
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=tokens,
                temperature=0.3,
                system="You are an AI assistant that generates GNU cobol code and return clean single markdown block.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": query
                            }
                        ]
                    }
                ]
            ).content[0].text
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")
        return response

    def chat(self, prompt, model):
        """
        Generic method to query any supported model.

        Args:
            prompt (str): The input prompt for the model
            model (str): The model to use (gpt-4o, gpt-35, claude-sonnet, claude-opus)

        Returns:
            str: The generated response content
        """
        api_config = load_dotenv(".env")
        if "gpt" in model:
            api_configs = {"API_KEY":api_config["GPT"]["API_KEY"], "model": model}
            return self.gpt(prompt, api_configs)

        elif "claude" in model:
            api_configs = {"API_KEY": api_config["CLAUDE"]["API_KEY"], "model": model}
            return self.claude(prompt, api_configs)
        elif "gemini" in model:
            api_configs = {"API_KEY": api_config["GEMINI"]["API_KEY"], "model": model}
            return self.gemini(prompt, api_configs)

        else:
            raise ValueError("Please select correct model from available models. \n1. gpt-4o\n2. gpt-35\n3. claude-sonnet\n4. claude-opus\n5. gemini-pro")