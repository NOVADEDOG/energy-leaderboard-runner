"""AMD GPU energy meter using ROCm-smi."""

import re
import shutil
import subprocess
import threading
import time
from typing import Dict, List, Optional

from .base import EnergyMeter


class RocmSmiMeter(EnergyMeter):
    """
    Energy meter implementation for AMD GPUs using rocm-smi.

    This meter uses the rocm-smi command-line tool to poll GPU power
    consumption at regular intervals and calculates total energy using
    trapezoidal integration.
    """

    def __init__(self, sampling_ms: int = 100, device_index: int = 0):
        """
        Initialize the ROCm-smi energy meter.

        Args:
            sampling_ms: Sampling interval in milliseconds (default: 100ms).
            device_index: GPU device index to monitor (default: 0).
        """
        self.sampling_ms = sampling_ms
        self.device_index = device_index
        self.thread: Optional[threading.Thread] = None
        self.power_samples: List[float] = []
        self.start_time: float = 0.0
        self.stop_time: float = 0.0
        self._running: bool = False

    def is_available(self) -> bool:
        """
        Check if rocm-smi is available on the system.

        Returns:
            bool: True if rocm-smi command is found in PATH.
        """
        return shutil.which("rocm-smi") is not None

    def start(self) -> None:
        """
        Start rocm-smi power monitoring in a background thread.

        Raises:
            RuntimeError: If rocm-smi is not available.
        """
        if not self.is_available():
            raise RuntimeError(
                "rocm-smi command not found. Please install ROCm tools. "
                "See RUNBOOK.md for installation instructions."
            )

        self._running = True
        self.power_samples = []
        self.start_time = time.time()

        # Start polling thread
        self.thread = threading.Thread(target=self._poll_power, daemon=True)
        self.thread.start()

    def _poll_power(self) -> None:
        """Poll AMD GPU power consumption in a background thread."""
        interval_s = self.sampling_ms / 1000.0

        while self._running:
            try:
                # Run rocm-smi to get power usage
                # -d: device index
                # -p: show power consumption
                result = subprocess.run(
                    ["rocm-smi", "-d", str(self.device_index), "-p"],
                    capture_output=True,
                    text=True,
                    timeout=1.0,
                )

                if result.returncode == 0:
                    power_watts = self._parse_power(result.stdout)
                    if power_watts is not None:
                        self.power_samples.append(power_watts)

            except (subprocess.TimeoutExpired, Exception):
                # If we can't read power, skip this sample
                pass

            time.sleep(interval_s)

    def _parse_power(self, output: str) -> Optional[float]:
        """
        Parse power consumption from rocm-smi output.

        Args:
            output: The stdout from rocm-smi command.

        Returns:
            Power in watts, or None if parsing fails.
        """
        # Look for patterns like "Average Graphics Package Power: 123.45 W"
        # or "Power: 123 W"
        patterns = [
            r"Average Graphics Package Power:\s+([\d.]+)\s*W",
            r"Power:\s+([\d.]+)\s*W",
            r"GPU Power:\s+([\d.]+)\s*W",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    def stop(self) -> Dict[str, float]:
        """
        Stop rocm-smi monitoring and calculate total energy consumed.

        Returns:
            Dictionary with energy_wh_raw, duration_s, and sampling_ms.
        """
        self.stop_time = time.time()
        self._running = False

        # Wait for polling thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        duration_s = self.stop_time - self.start_time

        # Calculate energy using trapezoidal integration
        if len(self.power_samples) < 2:
            return {
                "energy_wh_raw": 0.0,
                "duration_s": duration_s,
                "sampling_ms": self.sampling_ms,
            }

        # Power is already in watts
        power_watts = self.power_samples

        # Time between samples in hours
        dt_hours = (self.sampling_ms / 1000.0) / 3600.0

        # Trapezoidal integration
        energy_wh = 0.0
        for i in range(len(power_watts) - 1):
            avg_power = (power_watts[i] + power_watts[i + 1]) / 2.0
            energy_wh += avg_power * dt_hours

        return {
            "energy_wh_raw": energy_wh,
            "duration_s": duration_s,
            "sampling_ms": self.sampling_ms,
        }
