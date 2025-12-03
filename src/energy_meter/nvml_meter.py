"""NVIDIA GPU energy meter using NVML."""

import threading
import time
from typing import Dict, List, Optional

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

from .base import EnergyMeter


class NvmlMeter(EnergyMeter):
    """
    Energy meter implementation for NVIDIA GPUs using NVML.

    This meter uses the pynvml library to poll GPU power consumption
    at regular intervals and calculates total energy using trapezoidal integration.
    """

    def __init__(self, sampling_ms: int = 100, device_index: int = 0):
        """
        Initialize the NVIDIA NVML energy meter.

        Args:
            sampling_ms: Sampling interval in milliseconds (default: 100ms).
            device_index: GPU device index to monitor (default: 0).
        """
        self.sampling_ms = sampling_ms
        self.device_index = device_index
        self.handle: Optional[any] = None
        self.thread: Optional[threading.Thread] = None
        self.power_samples: List[float] = []
        self.start_time: float = 0.0
        self.stop_time: float = 0.0
        self._running: bool = False
        self._nvml_initialized: bool = False

    def is_available(self) -> bool:
        """
        Check if NVML is available and can access NVIDIA GPUs.

        Returns:
            bool: True if NVML can be initialized.
        """
        if not NVML_AVAILABLE:
            return False

        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            pynvml.nvmlShutdown()
            return device_count > 0
        except Exception:
            return False

    def start(self) -> None:
        """
        Start NVML power monitoring in a background thread.

        Raises:
            RuntimeError: If NVML cannot be initialized or GPU is not accessible.
        """
        if not NVML_AVAILABLE:
            raise RuntimeError("pynvml is not installed. Install with: pip install pynvml")

        try:
            pynvml.nvmlInit()
            self._nvml_initialized = True
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize NVML: {e}")

        self._running = True
        self.power_samples = []
        self.start_time = time.time()

        # Start polling thread
        self.thread = threading.Thread(target=self._poll_power, daemon=True)
        self.thread.start()

    def _poll_power(self) -> None:
        """Poll GPU power consumption in a background thread."""
        interval_s = self.sampling_ms / 1000.0

        while self._running:
            try:
                # Get power in milliwatts
                power_mw = pynvml.nvmlDeviceGetPowerUsage(self.handle)
                self.power_samples.append(power_mw)
            except Exception:
                # If we can't read power, skip this sample
                pass

            time.sleep(interval_s)

    def stop(self) -> Dict[str, float]:
        """
        Stop NVML monitoring and calculate total energy consumed.

        Returns:
            Dictionary with energy_wh_raw, duration_s, and sampling_ms.

        Raises:
            RuntimeError: If NVML cleanup fails.
        """
        self.stop_time = time.time()
        self._running = False

        # Wait for polling thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        # Shutdown NVML
        if self._nvml_initialized:
            try:
                pynvml.nvmlShutdown()
                self._nvml_initialized = False
            except Exception:
                pass

        duration_s = self.stop_time - self.start_time

        # Calculate energy using trapezoidal integration
        if len(self.power_samples) < 2:
            return {
                "energy_wh_raw": 0.0,
                "duration_s": duration_s,
                "sampling_ms": self.sampling_ms,
            }

        # Convert power from milliwatts to watts
        power_watts = [p / 1000.0 for p in self.power_samples]

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
