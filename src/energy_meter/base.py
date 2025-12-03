"""Abstract base class for energy meters."""

from abc import ABC, abstractmethod
from typing import Dict


class EnergyMeter(ABC):
    """Abstract base class for all energy meter implementations."""

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this meter is available on the current system.

        Returns:
            bool: True if the meter can be used on this system.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        Start the energy measurement process.

        This may involve starting a subprocess, initializing hardware
        interfaces, or beginning a polling thread.

        Raises:
            RuntimeError: If the meter cannot be started.
        """
        pass

    @abstractmethod
    def stop(self) -> Dict[str, float]:
        """
        Stop the energy measurement and return the collected metrics.

        Returns:
            A dictionary containing at minimum:
            - energy_wh_raw (float): Raw energy consumption in watt-hours.
            - duration_s (float): Duration of measurement in seconds.
            - sampling_ms (int): Sampling interval used in milliseconds.

        Raises:
            RuntimeError: If the meter cannot be stopped or data cannot be retrieved.
        """
        pass
