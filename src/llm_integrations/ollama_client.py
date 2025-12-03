"""Ollama LLM integration implementation."""

import time
from typing import Tuple

import ollama

from .base import LlmRunner


class OllamaClient(LlmRunner):
    """
    Implementation of LlmRunner for Ollama.

    This client connects to a locally running Ollama instance
    and executes prompts using the Ollama Python client library.
    """

    def __init__(self, host: str):
        """
        Initialize the Ollama client.

        Args:
            host: The Ollama host URL (e.g., "http://localhost:11434").
        """
        self.host = host
        self.client = ollama.Client(host=host)

    def check_connection(self) -> bool:
        """
        Check if the Ollama service is available and responding.

        Returns:
            bool: True if connection is successful.

        Raises:
            ConnectionError: If the Ollama service cannot be reached.
        """
        try:
            # Try to list models as a connection check
            self.client.list()
            return True
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Ollama at {self.host}. "
                f"Please ensure Ollama is running. Error: {e}"
            )

    def generate(
        self, model: str, prompt: str
    ) -> Tuple[str, int, int, float]:
        """
        Generate a completion for the given prompt using the specified model.

        Args:
            model: The model identifier (e.g., "llama3:latest").
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

            response = self.client.generate(
                model=model,
                prompt=prompt,
            )

            end_time = time.time()
            response_time_s = end_time - start_time

            # Extract metrics from response
            completion_text = response.get("response", "")
            tokens_prompt = response.get("prompt_eval_count", 0)
            tokens_completion = response.get("eval_count", 0)

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
