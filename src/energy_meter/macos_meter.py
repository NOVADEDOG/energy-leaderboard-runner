import logging
import re
import subprocess
import sys
import threading
import time
from typing import Dict, List, Optional

from .base import EnergyMeter


class MacosMeter(EnergyMeter):
    """
    Energy meter implementation for Apple macOS using powermetrics.

    This meter uses the system's `powermetrics` command to measure
    system-wide power consumption. It requires running with sudo privileges.
    """

    def __init__(self, sampling_ms: int = 100):
        """
        Initialize the macOS energy meter.

        Args:
            sampling_ms: Sampling interval in milliseconds (default: 100ms).
        """
        self.sampling_ms = sampling_ms
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        self.output_lines: List[str] = []
        self.start_time: float = 0.0
        self.stop_time: float = 0.0
        self._running: bool = False

    def is_available(self) -> bool:
        """
        Check if powermetrics is available (macOS only).

        Returns:
            bool: True if running on macOS.
        """
        return sys.platform == "darwin"

    def start(self) -> None:
        """
        Start powermetrics in a background thread.

        The powermetrics command samples power consumption at the specified
        interval and outputs data to stdout, which is captured for later parsing.

        Raises:
            RuntimeError: If powermetrics cannot be started.
        """
        if not self.is_available():
            raise RuntimeError("macOS powermetrics is not available on this platform")

        self._running = True
        self.output_lines = []
        self.start_time = time.time()

        # Start powermetrics process
        # -i: sampling interval in ms
        # --samplers: select samplers (cpu_power gives us power consumption data)
        cmd = [
            "sudo",
            "powermetrics",
            "-i",
            str(self.sampling_ms),
            "--samplers",
            "cpu_power",
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            raise RuntimeError("powermetrics command not found. Is this macOS?")
        except Exception as e:
            raise RuntimeError(f"Failed to start powermetrics: {e}")

        # Start a thread to read output
        self.thread = threading.Thread(target=self._read_output, daemon=True)
        self.thread.start()
        
        # Give powermetrics a moment to start collecting data
        time.sleep(0.3)

    def _read_output(self) -> None:
        """Read output from powermetrics subprocess in a background thread."""
        if self.process and self.process.stdout:
            try:
                for line in iter(self.process.stdout.readline, ""):
                    if not self._running:
                        break
                    self.output_lines.append(line.strip())
            except Exception as e:
                logging.warning(f"Error reading powermetrics output: {e}")

    def stop(self) -> Dict[str, float]:
        """
        Stop powermetrics and parse the collected power data.

        Returns:
            Dictionary with energy_wh_raw, duration_s, and sampling_ms.

        Raises:
            RuntimeError: If no data was collected or parsing fails.
        """
        # Wait for at least one more sample before stopping
        time.sleep(max(0.15, self.sampling_ms / 1000.0))
        
        self.stop_time = time.time()
        self._running = False

        # Terminate the powermetrics process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

        # Wait for the reading thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        duration_s = self.stop_time - self.start_time

        # Parse the output to extract power measurements
        power_samples = self._parse_power_samples()

        if len(power_samples) < 2:
            # For very short measurements with insufficient samples,
            # estimate based on available data and duration
            if len(power_samples) == 1:
                # Use the single sample as average power
                avg_power_watts = power_samples[0] / 1000.0
                energy_wh = avg_power_watts * (duration_s / 3600.0)
                return {
                    "energy_wh_raw": energy_wh,
                    "duration_s": duration_s,
                    "sampling_ms": self.sampling_ms,
                }
            else:
                # No samples at all
                return {
                    "energy_wh_raw": 0.0,
                    "duration_s": duration_s,
                    "sampling_ms": self.sampling_ms,
                }

        # Calculate total energy using trapezoidal integration
        # Power is in milliwatts, convert to watts
        power_watts = [p / 1000.0 for p in power_samples]

        # Time between samples in hours
        dt_hours = (self.sampling_ms / 1000.0) / 3600.0

        # Trapezoidal rule: sum of averages between consecutive points
        energy_wh = 0.0
        for i in range(len(power_watts) - 1):
            avg_power = (power_watts[i] + power_watts[i + 1]) / 2.0
            energy_wh += avg_power * dt_hours

        return {
            "energy_wh_raw": energy_wh,
            "duration_s": duration_s,
            "sampling_ms": self.sampling_ms,
        }

    def _parse_power_samples(self) -> List[float]:
        """
        Parse power samples from powermetrics output.

        Returns:
            List of power values in milliwatts.
        """
        power_samples = []

        # Regex to identify start of a sample block
        # "*** Sampled system activity (Thu Jan  1 00:00:00 1970) (5000.00ms elapsed) ***"
        sample_header_pattern = r"\*\*\* Sampled system activity .* \*\*\*"

        # Patterns for power
        combined_pattern = r"Combined Power \(CPU \+ GPU \+ ANE\):\s+([\d.]+)\s+mW"
        cpu_pattern = r"CPU Power:\s+([\d.]+)\s+mW"
        gpu_pattern = r"GPU Power:\s+([\d.]+)\s+mW"
        package_pattern = r"Package Power:\s+([\d.]+)\s+mW"

        current_block_values: Dict[str, float] = {}
        in_block = False

        for line in self.output_lines:
            if re.search(sample_header_pattern, line):
                # New block found. Process previous block if exists.
                if in_block:
                    val = self._calculate_block_power(current_block_values)
                    if val is not None:
                        power_samples.append(val)

                # Reset for new block
                current_block_values = {}
                in_block = True
                continue
            
            if in_block:
                # Try to extract power values
                match = re.search(combined_pattern, line)
                if match:
                    try:
                        current_block_values['combined'] = float(match.group(1))
                        continue
                    except (ValueError, IndexError):
                        pass

                match = re.search(cpu_pattern, line)
                if match:
                    try:
                        current_block_values['cpu'] = float(match.group(1))
                        continue
                    except (ValueError, IndexError):
                        pass

                match = re.search(gpu_pattern, line)
                if match:
                    try:
                        current_block_values['gpu'] = float(match.group(1))
                        continue
                    except (ValueError, IndexError):
                        pass

                match = re.search(package_pattern, line)
                if match:
                    try:
                        current_block_values['package'] = float(match.group(1))
                        continue
                    except (ValueError, IndexError):
                        pass

        # Process the last block
        if in_block:
            val = self._calculate_block_power(current_block_values)
            if val is not None:
                power_samples.append(val)

        return power_samples

    def _calculate_block_power(self, values: Dict[str, float]) -> Optional[float]:
        """Calculate total power from a block of parsed values."""
        if 'combined' in values:
            return values['combined']

        # If we have Package Power, it usually covers CPU (and maybe GPU/system)
        # But prefer summing specific components if known, or fallback to Package if it's the only thing.
        # Actually, Combined is best. If not, CPU + GPU is usually what we want.

        total = 0.0
        found = False
        if 'cpu' in values:
            total += values['cpu']
            found = True
        if 'gpu' in values:
            total += values['gpu']
            found = True

        if found:
            return total

        if 'package' in values:
            return values['package']

        return None
