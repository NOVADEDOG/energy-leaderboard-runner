"""
Device information detection utilities.

Automatically detects hardware details for benchmark result attribution.
Falls back to user-provided values if auto-detection fails.
"""

import os
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceInfo:
    """Device information for benchmark attribution."""
    
    # Required fields
    device_name: str          # Human-readable device name (e.g., "Apple M1 MacBook Air")
    device_type: str          # Category: "apple", "nvidia", "amd", "intel", "unknown"
    os_name: str              # Operating system name
    os_version: str           # Operating system version
    
    # Optional detailed fields
    cpu_model: Optional[str] = None     # CPU model string
    gpu_model: Optional[str] = None     # GPU model string (if applicable)
    ram_gb: Optional[float] = None      # Total RAM in GB
    chip_architecture: Optional[str] = None  # arm64, x86_64, etc.
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "device_name": self.device_name,
            "device_type": self.device_type,
            "os_name": self.os_name,
            "os_version": self.os_version,
        }
        if self.cpu_model:
            result["cpu_model"] = self.cpu_model
        if self.gpu_model:
            result["gpu_model"] = self.gpu_model
        if self.ram_gb:
            result["ram_gb"] = self.ram_gb
        if self.chip_architecture:
            result["chip_architecture"] = self.chip_architecture
        return result


def _run_command(cmd: list[str], timeout: int = 5) -> Optional[str]:
    """Run a shell command and return output, or None on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _detect_macos_device() -> DeviceInfo:
    """Detect device info on macOS."""
    os_name = "macOS"
    os_version = platform.mac_ver()[0] or "Unknown"
    chip_arch = platform.machine()
    
    # Get hardware model
    hw_model = _run_command(["sysctl", "-n", "hw.model"]) or "Unknown Mac"
    
    # Get CPU brand
    cpu_brand = _run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
    
    # Check for Apple Silicon
    chip_name = None
    if chip_arch == "arm64":
        # Try to get Apple Silicon chip name
        chip_info = _run_command(["system_profiler", "SPHardwareDataType"])
        if chip_info:
            for line in chip_info.split("\n"):
                if "Chip:" in line or "Processor Name:" in line:
                    chip_name = line.split(":")[-1].strip()
                    break
    
    # Determine device type
    if chip_arch == "arm64" or (chip_name and "Apple" in chip_name):
        device_type = "apple"
        cpu_model = chip_name or "Apple Silicon"
    else:
        device_type = "intel"
        cpu_model = cpu_brand
    
    # Get RAM
    ram_bytes = _run_command(["sysctl", "-n", "hw.memsize"])
    ram_gb = None
    if ram_bytes:
        try:
            ram_gb = round(int(ram_bytes) / (1024**3), 1)
        except ValueError:
            pass
    
    # Build device name
    if chip_name:
        device_name = f"{chip_name} Mac ({hw_model})"
    else:
        device_name = f"Mac ({hw_model})"
    
    return DeviceInfo(
        device_name=device_name,
        device_type=device_type,
        os_name=os_name,
        os_version=os_version,
        cpu_model=cpu_model,
        gpu_model=chip_name if device_type == "apple" else None,  # Apple Silicon is unified
        ram_gb=ram_gb,
        chip_architecture=chip_arch,
    )


def _detect_linux_device() -> DeviceInfo:
    """Detect device info on Linux."""
    os_name = "Linux"
    os_version = platform.release()
    chip_arch = platform.machine()
    
    # Get CPU info
    cpu_model = None
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu_model = line.split(":")[-1].strip()
                    break
    except (IOError, OSError):
        pass
    
    # Get RAM
    ram_gb = None
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    mem_kb = int(line.split()[1])
                    ram_gb = round(mem_kb / (1024**2), 1)
                    break
    except (IOError, OSError, ValueError):
        pass
    
    # Detect GPU and determine device type
    device_type = "unknown"
    gpu_model = None
    
    # Check for NVIDIA GPU
    nvidia_info = _run_command(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
    if nvidia_info:
        gpu_model = nvidia_info.split("\n")[0].strip()
        device_type = "nvidia"
    
    # Check for AMD GPU if no NVIDIA
    if not gpu_model:
        rocm_info = _run_command(["rocm-smi", "--showproductname"])
        if rocm_info:
            for line in rocm_info.split("\n"):
                if "GPU" in line or "Radeon" in line or "Instinct" in line:
                    gpu_model = line.strip()
                    device_type = "amd"
                    break
    
    # If no GPU detected, classify by CPU
    if device_type == "unknown":
        if cpu_model:
            cpu_lower = cpu_model.lower()
            if "intel" in cpu_lower:
                device_type = "intel"
            elif "amd" in cpu_lower:
                device_type = "amd"
    
    # Build device name
    if gpu_model:
        device_name = f"Linux with {gpu_model}"
    elif cpu_model:
        # Shorten CPU name
        short_cpu = cpu_model.split("@")[0].strip()
        device_name = f"Linux with {short_cpu}"
    else:
        device_name = f"Linux ({chip_arch})"
    
    return DeviceInfo(
        device_name=device_name,
        device_type=device_type,
        os_name=os_name,
        os_version=os_version,
        cpu_model=cpu_model,
        gpu_model=gpu_model,
        ram_gb=ram_gb,
        chip_architecture=chip_arch,
    )


def _detect_windows_device() -> DeviceInfo:
    """Detect device info on Windows."""
    os_name = "Windows"
    os_version = platform.version()
    chip_arch = platform.machine()
    
    # Get CPU info via wmic
    cpu_model = _run_command(["wmic", "cpu", "get", "name"])
    if cpu_model:
        # Parse wmic output (skip header line)
        lines = [l.strip() for l in cpu_model.split("\n") if l.strip()]
        if len(lines) > 1:
            cpu_model = lines[1]
        else:
            cpu_model = lines[0] if lines else None
    
    # Get RAM via wmic
    ram_gb = None
    ram_info = _run_command(["wmic", "computersystem", "get", "totalphysicalmemory"])
    if ram_info:
        lines = [l.strip() for l in ram_info.split("\n") if l.strip()]
        if len(lines) > 1:
            try:
                ram_gb = round(int(lines[1]) / (1024**3), 1)
            except ValueError:
                pass
    
    # Detect GPU
    device_type = "unknown"
    gpu_model = None
    
    # Check NVIDIA
    nvidia_info = _run_command(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
    if nvidia_info:
        gpu_model = nvidia_info.split("\n")[0].strip()
        device_type = "nvidia"
    
    # Classify by CPU if no GPU
    if device_type == "unknown" and cpu_model:
        cpu_lower = cpu_model.lower()
        if "intel" in cpu_lower:
            device_type = "intel"
        elif "amd" in cpu_lower:
            device_type = "amd"
    
    # Build device name
    if gpu_model:
        device_name = f"Windows PC with {gpu_model}"
    elif cpu_model:
        short_cpu = cpu_model.split("@")[0].strip()
        device_name = f"Windows PC with {short_cpu}"
    else:
        device_name = f"Windows PC ({chip_arch})"
    
    return DeviceInfo(
        device_name=device_name,
        device_type=device_type,
        os_name=os_name,
        os_version=os_version,
        cpu_model=cpu_model,
        gpu_model=gpu_model,
        ram_gb=ram_gb,
        chip_architecture=chip_arch,
    )


def detect_device_info() -> DeviceInfo:
    """
    Auto-detect device information for the current platform.
    
    Returns:
        DeviceInfo with populated fields based on platform detection.
    """
    system = platform.system()
    
    if system == "Darwin":
        return _detect_macos_device()
    elif system == "Linux":
        return _detect_linux_device()
    elif system == "Windows":
        return _detect_windows_device()
    else:
        # Fallback for unknown platforms
        return DeviceInfo(
            device_name=f"Unknown ({platform.platform()})",
            device_type="unknown",
            os_name=system,
            os_version=platform.version(),
            chip_architecture=platform.machine(),
        )


def get_device_info(
    device_name: Optional[str] = None,
    device_type: Optional[str] = None,
) -> DeviceInfo:
    """
    Get device information, using auto-detection with optional overrides.
    
    Args:
        device_name: Optional override for device name.
        device_type: Optional override for device type.
    
    Returns:
        DeviceInfo with auto-detected or overridden values.
    """
    info = detect_device_info()
    
    if device_name:
        info.device_name = device_name
    if device_type:
        info.device_type = device_type
    
    return info
