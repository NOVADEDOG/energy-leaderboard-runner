"""Configuration management for the energy-leaderboard-runner."""

import os
from typing import Optional


class Config:
    """Central configuration for the application."""

    # Ollama connection settings
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # CO2 emission calculations
    # Default: EU average grid intensity (g CO2 per kWh)
    CO2_INTENSITY_G_KWH: float = float(
        os.getenv("CO2_INTENSITY_G_KWH", "350.0")
    )

    # Region identifier for reporting
    REGION: str = os.getenv("REGION", "unknown")

    # Energy meter sampling interval in milliseconds
    SAMPLING_INTERVAL_MS: int = int(os.getenv("SAMPLING_INTERVAL_MS", "100"))

    @classmethod
    def get_ollama_host(cls) -> str:
        """Get the Ollama host URL."""
        return cls.OLLAMA_HOST

    @classmethod
    def get_co2_intensity(cls) -> float:
        """Get the CO2 grid intensity in g/kWh."""
        return cls.CO2_INTENSITY_G_KWH

    @classmethod
    def get_region(cls) -> str:
        """Get the region identifier."""
        return cls.REGION

    @classmethod
    def get_sampling_interval_ms(cls) -> int:
        """Get the energy meter sampling interval in milliseconds."""
        return cls.SAMPLING_INTERVAL_MS


# Global config instance
config = Config()
