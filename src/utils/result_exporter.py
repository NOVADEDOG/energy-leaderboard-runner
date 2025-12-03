"""Result export and metrics calculation utilities."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import jsonschema


def export_results(
    results_list: List[Dict],
    output_file: str,
    co2_intensity: float,
    schema_path: Optional[str] = None,
) -> None:
    """
    Calculate derived metrics and export results to a JSON file.

    This function takes a list of raw measurement results, calculates
    derived metrics (wh_per_1k_tokens, energy_kwh_per_token, g_co2),
    validates against the schema, and writes to the output file.

    Args:
        results_list: List of result dictionaries with raw measurements.
        output_file: Path to the output JSON file.
        co2_intensity: Grid CO2 intensity in g/kWh for emissions calculations.
        schema_path: Optional path to JSON schema file for validation.

    Raises:
        ValueError: If validation against schema fails.
        IOError: If the output file cannot be written.
    """
    # Calculate derived metrics for each result
    enriched_results = []

    for result in results_list:
        # Extract raw values
        tokens_prompt = result.get("tokens_prompt", 0)
        tokens_completion = result.get("tokens_completion", 0)
        energy_wh_raw = result.get("energy_wh_raw", 0.0)
        energy_wh_net = result.get("energy_wh_net", energy_wh_raw)

        # Calculate total tokens
        total_tokens = tokens_prompt + tokens_completion

        # Calculate derived metrics
        if total_tokens > 0:
            wh_per_1k_tokens = (energy_wh_net / total_tokens) * 1000.0
            energy_kwh_per_token = (energy_wh_net / 1000.0) / total_tokens
        else:
            wh_per_1k_tokens = 0.0
            energy_kwh_per_token = 0.0

        # Calculate CO2 emissions (energy_wh_net → kWh → g CO2)
        energy_kwh = energy_wh_net / 1000.0
        g_co2 = energy_kwh * co2_intensity

        # Create enriched result
        enriched = {
            **result,
            "wh_per_1k_tokens": round(wh_per_1k_tokens, 6),
            "energy_kwh_per_token": round(energy_kwh_per_token, 9),
            "g_co2": round(g_co2, 6),
        }

        enriched_results.append(enriched)

    # Validate against schema if provided
    if schema_path:
        try:
            with open(schema_path, "r") as f:
                schema = json.load(f)
            jsonschema.validate(instance=enriched_results, schema=schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Results do not conform to schema: {e.message}")
        except FileNotFoundError:
            raise ValueError(f"Schema file not found: {schema_path}")

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    try:
        with open(output_file, "w") as f:
            json.dump(enriched_results, f, indent=2)
    except Exception as e:
        raise IOError(f"Failed to write results to {output_file}: {e}")


def validate_result_schema(results: List[Dict], schema_path: str) -> bool:
    """
    Validate a list of results against a JSON schema.

    Args:
        results: List of result dictionaries.
        schema_path: Path to the JSON schema file.

    Returns:
        bool: True if validation succeeds.

    Raises:
        ValueError: If validation fails.
    """
    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
        jsonschema.validate(instance=results, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        raise ValueError(f"Validation error: {e.message}")
    except FileNotFoundError:
        raise ValueError(f"Schema file not found: {schema_path}")
