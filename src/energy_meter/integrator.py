"""Platform detection and energy meter integration."""

import sys
from typing import Optional

from .base import EnergyMeter
from .macos_meter import MacosMeter
from .nvml_meter import NvmlMeter
from .rapl_meter import RaplMeter
from .rocm_smi_meter import RocmSmiMeter


def get_platform_meter(sampling_ms: int = 100) -> EnergyMeter:
    """
    Detect the current platform and return the appropriate energy meter.

    This function checks the operating system and available hardware,
    then returns an instance of the appropriate EnergyMeter implementation.

    The priority order for Linux is:
    1. NVIDIA GPU (NVML)
    2. AMD GPU (ROCm-smi)
    3. Intel/AMD CPU (RAPL)

    Args:
        sampling_ms: Sampling interval in milliseconds for the meter.

    Returns:
        An instance of a concrete EnergyMeter implementation.

    Raises:
        NotImplementedError: If no suitable energy meter is found for the platform.
    """
    # Check macOS
    if sys.platform == "darwin":
        meter = MacosMeter(sampling_ms=sampling_ms)
        if meter.is_available():
            return meter

    # Check Linux meters in priority order
    if sys.platform == "linux":
        # Try NVIDIA GPU first
        nvml_meter = NvmlMeter(sampling_ms=sampling_ms)
        if nvml_meter.is_available():
            return nvml_meter

        # Try AMD GPU
        rocm_meter = RocmSmiMeter(sampling_ms=sampling_ms)
        if rocm_meter.is_available():
            return rocm_meter

        # Try CPU RAPL
        rapl_meter = RaplMeter(sampling_ms=sampling_ms)
        if rapl_meter.is_available():
            return rapl_meter

        # No Linux meter found
        raise NotImplementedError(
            "No energy meter available on this Linux system. "
            "Supported: NVIDIA GPU (NVML), AMD GPU (ROCm-smi), Intel/AMD CPU (RAPL). "
            "Please check that appropriate drivers and tools are installed. "
            "See RUNBOOK.md for troubleshooting."
        )

    # No suitable meter found for this platform
    raise NotImplementedError(
        f"No energy meter available for platform: {sys.platform}. "
        f"Supported platforms: macOS (darwin), Linux. "
        f"Windows support is not currently planned."
    )
