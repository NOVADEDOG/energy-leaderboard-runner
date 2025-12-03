"""OpenAI-compatible LLM integration implementation."""

import time
from typing import Tuple, Optional

import openai
from openai import OpenAI

from .base import LlmRunner


class OpenAIClient(LlmRunner):
    """
    Implementation of LlmRunner for OpenAI-compatible APIs.
    
    This client connects to any OpenAI-compatible endpoint (e.g., vLLM, AnythingLLM,
    local servers) and executes prompts.
    """

    def __init__(self, base_url: str, api_key: str = "sk-no-key-required"):
        """
        Initialize the OpenAI client.

        Args:
            base_url: The base URL for the API (e.g., "http://localhost:8000/v1").
            api_key: API key if required (default: dummy key for local servers).
        """
        self.base_url = base_url
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def check_connection(self) -> bool:
        """
        Check if the service is available and responding.

        Returns:
            bool: True if connection is successful.

        Raises:
            ConnectionError: If the service cannot be reached.
        """
        try:
            # Try to list models as a connection check
            self.client.models.list()
            return True
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to OpenAI-compatible API at {self.base_url}. "
                f"Error: {e}"
            )

    def generate(
        self, model: str, prompt: str
    ) -> Tuple[str, int, int, float]:
        """
        Generate a completion for the given prompt using the specified model.

        Args:
            model: The model identifier.
            prompt: The input prompt text.

        Returns:
            A tuple containing:
            - completion_text (str): The generated text.
            - tokens_prompt (int): Number of tokens in the prompt.
            - tokens_completion (int): Number of tokens in the completion.
            - response_time_s (float): Time taken to generate the response in seconds.

        Raises:
            RuntimeError: If generation fails.
        """
        try:
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )

            end_time = time.time()
            response_time_s = end_time - start_time

            # Extract metrics from response
            choice = response.choices[0]
            completion_text = choice.message.content or ""
            
            # Usage stats might be None for some local servers
            usage = response.usage
            tokens_prompt = usage.prompt_tokens if usage else 0
            tokens_completion = usage.completion_tokens if usage else 0

            return (
                completion_text,
                tokens_prompt,
                tokens_completion,
                response_time_s,
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to generate completion with model '{model}'. Error: {e}"
            )
