"""Intel/AMD CPU energy meter using RAPL (Running Average Power Limit)."""

import glob
import os
import time
from pathlib import Path
from typing import Dict, Optional

from .base import EnergyMeter


class RaplMeter(EnergyMeter):
    """
    Energy meter implementation for Intel/AMD CPUs using RAPL.

    This meter reads energy counters from the Linux kernel's powercap
    interface at /sys/class/powercap/intel-rapl/. It measures the
    difference in energy counter values between start and stop.
    """

    def __init__(self, sampling_ms: int = 100):
        """
        Initialize the RAPL energy meter.

        Args:
            sampling_ms: Sampling interval (not used for RAPL, but kept for consistency).
        """
        self.sampling_ms = sampling_ms
        self.rapl_path: Optional[Path] = None
        self.start_energy_uj: float = 0.0
        self.start_time: float = 0.0
        self.stop_time: float = 0.0

    def is_available(self) -> bool:
        """
        Check if RAPL interface is available on this system.

        Returns:
            bool: True if /sys/class/powercap/intel-rapl/ exists and has energy counters.
        """
        # Look for intel-rapl directory
        rapl_base = Path("/sys/class/powercap")
        if not rapl_base.exists():
            return False

        # Find RAPL zones
        rapl_zones = list(rapl_base.glob("intel-rapl:*"))

        # Check if any zone has an energy_uj file
        for zone in rapl_zones:
            energy_file = zone / "energy_uj"
            if energy_file.exists():
                self.rapl_path = zone
                return True

        return False

    def start(self) -> None:
        """
        Start RAPL energy measurement by reading the current energy counter.

        Raises:
            RuntimeError: If RAPL interface is not available.
            PermissionError: If RAPL files are not readable.
        """
        if not self.is_available():
            raise RuntimeError(
                "RAPL interface not available. "
                "Ensure you're on a Linux system with Intel/AMD CPU."
            )

        # Check permissions explicitly
        if self.rapl_path:
            energy_file = self.rapl_path / "energy_uj"
            if not os.access(energy_file, os.R_OK):
                raise PermissionError(
                    f"Permission denied reading {energy_file}. "
                    "Please run with sudo or check permissions."
                )

        self.start_time = time.time()

        # Read initial energy value
        self.start_energy_uj = self._read_energy_uj()

    def _read_energy_uj(self) -> float:
        """
        Read the current energy counter value in microjoules.

        Returns:
            Energy counter value in microjoules.

        Raises:
            RuntimeError: If reading fails.
        """
        if self.rapl_path is None:
            raise RuntimeError("RAPL path not initialized")

        energy_file = self.rapl_path / "energy_uj"

        try:
            with open(energy_file, "r") as f:
                energy_uj_str = f.read().strip()
                return float(energy_uj_str)
        except Exception as e:
            raise RuntimeError(f"Failed to read RAPL energy counter: {e}")

    def stop(self) -> Dict[str, float]:
        """
        Stop RAPL measurement and calculate energy consumed.

        The energy is calculated as the difference between the stop
        and start counter values, converted from microjoules to watt-hours.

        Returns:
            Dictionary with energy_wh_raw, duration_s, and sampling_ms.

        Raises:
            RuntimeError: If reading the energy counter fails.
        """
        self.stop_time = time.time()

        # Read final energy value
        stop_energy_uj = self._read_energy_uj()

        duration_s = self.stop_time - self.start_time

        # Calculate energy difference in microjoules
        energy_diff_uj = stop_energy_uj - self.start_energy_uj

        # Handle counter wrap-around (RAPL counters can overflow)
        # Typical RAPL counter max is around 2^32 microjoules
        if energy_diff_uj < 0:
            # Assume counter wrapped once
            max_counter = 2**32
            energy_diff_uj += max_counter

        # Convert microjoules to watt-hours
        # 1 Wh = 3,600,000,000 microjoules
        energy_wh = energy_diff_uj / 3_600_000_000.0

        return {
            "energy_wh_raw": energy_wh,
            "duration_s": duration_s,
            "sampling_ms": self.sampling_ms,
        }
