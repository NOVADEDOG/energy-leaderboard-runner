"""Abstract base class for LLM runners."""

from abc import ABC, abstractmethod
from typing import Tuple


class LlmRunner(ABC):
    """Abstract base class for all LLM integration implementations."""

    @abstractmethod
    def check_connection(self) -> bool:
        """
        Check if the LLM service is available and responding.

        Returns:
            bool: True if connection is successful, False otherwise.

        Raises:
            ConnectionError: If the service cannot be reached.
        """
        pass

    @abstractmethod
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
        pass
