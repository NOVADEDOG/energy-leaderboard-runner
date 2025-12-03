/**
 * Data loader for benchmark results
 * Fetches JSON files from the data/ directory at runtime
 */

import type { BenchmarkResult, BenchmarkRun, ModelStats, DeviceType } from './types';

/**
 * Load all benchmark results from the data directory
 */
export async function loadAllBenchmarks(): Promise<{ filename: string; results: BenchmarkRun }[]> {
    const benchmarks: { filename: string; results: BenchmarkRun }[] = [];
    const baseUrl = import.meta.env.BASE_URL || '/';

    try {
        // Fetch the manifest to get the list of files
        const manifestResponse = await fetch(`${baseUrl}data/manifest.json`);
        if (!manifestResponse.ok) {
            console.warn('Failed to load manifest.json, falling back to empty list');
            return [];
        }
        const files: string[] = await manifestResponse.json();

        const loadPromises = files.map(async (filename) => {
            try {
                const response = await fetch(`${baseUrl}data/${filename}`);
                if (!response.ok) {
                    console.warn(`Failed to load ${filename}: ${response.status}`);
                    return null;
                }
                const data = await response.json();
                return { filename, results: data as BenchmarkRun };
            } catch (error) {
                console.warn(`Error loading ${filename}:`, error);
                return null;
            }
        });

        const results = await Promise.all(loadPromises);

        for (const result of results) {
            if (result) {
                benchmarks.push(result);
            }
        }
    } catch (error) {
        console.error('Error loading benchmarks:', error);
    }

    return benchmarks;
}

/**
 * Detect device type from filename, model info, or device_type field
 */
export function detectDeviceType(result: BenchmarkResult, filename: string): DeviceType {
    // First check if device_type is in the result (new schema)
    if (result.device_type && ['apple', 'nvidia', 'amd', 'intel', 'unknown'].includes(result.device_type)) {
        return result.device_type as DeviceType;
    }

    // Fallback to filename/model detection (legacy data)
    const combined = (filename + result.model + (result.gpu_model || '') + (result.cpu_model || '')).toLowerCase();

    if (combined.includes('apple') || combined.includes('m1') || combined.includes('m2') || combined.includes('m3') || combined.includes('mac')) {
        return 'apple';
    }
    if (combined.includes('nvidia') || combined.includes('rtx') || combined.includes('gtx') || combined.includes('t4') || combined.includes('a100')) {
        return 'nvidia';
    }
    if (combined.includes('amd') || combined.includes('radeon') || combined.includes('rocm')) {
        return 'amd';
    }
    if (combined.includes('intel') || combined.includes('cpu') || combined.includes('rapl') || combined.includes('xeon')) {
        return 'intel';
    }

    return 'unknown';
}

/**
 * Determine if results are from real power measurements or estimated
 * Real measurements have sampling_ms and typically more accurate energy data
 */
export function isMeasuredData(results: BenchmarkResult[]): boolean {
    // If any result has a notice indicating estimation, mark as estimated
    const hasEstimationNotice = results.some(r =>
        r.notice?.toLowerCase().includes('estimated') ||
        r.notice?.toLowerCase().includes('simulated')
    );

    if (hasEstimationNotice) return false;

    // If we have sampling data and energy readings, consider it measured
    return results.every(r => r.sampling_ms > 0 && r.energy_wh_raw > 0);
}

/**
 * Aggregate benchmark results by model to create leaderboard stats
 */
export function aggregateByModel(
    benchmarks: { filename: string; results: BenchmarkRun }[]
): ModelStats[] {
    const modelMap = new Map<string, {
        results: BenchmarkResult[];
        filenames: Set<string>;
        testsets: Set<string>;
    }>();

    // Group results by model + provider + device
    for (const { filename, results } of benchmarks) {
        for (const result of results) {
            // Create a unique key for the model configuration
            // We group by Model + Provider + Device Type to avoid mixing different hardware results
            const deviceType = detectDeviceType(result, filename);
            const key = `${result.model}__${result.provider}__${deviceType}`;

            if (!modelMap.has(key)) {
                modelMap.set(key, {
                    results: [],
                    filenames: new Set(),
                    testsets: new Set()
                });
            }

            const group = modelMap.get(key)!;
            group.results.push(result);
            group.filenames.add(filename);

            if (result.testset_name) {
                group.testsets.add(result.testset_name);
            }
        }
    }

    // Calculate aggregated stats for each model group
    const stats: ModelStats[] = [];

    for (const [, { results, filenames, testsets }] of modelMap) {
        const firstResult = results[0];
        const model = firstResult.model;
        const provider = firstResult.provider;
        const region = firstResult.region;
        // const testsetName = firstResult.testset_name; // Removed in favor of aggregated testsets

        // Extract device info (use first result, or fallback to detection)
        // Note: Since we grouped by device type, this should be consistent
        const filename = Array.from(filenames)[0]; // Use first filename for detection fallback
        const deviceType = detectDeviceType(firstResult, filename);
        const deviceName = firstResult.device_name || `Unknown (${filename})`;
        const osName = firstResult.os_name || 'Unknown';
        const osVersion = firstResult.os_version || '';
        const cpuModel = firstResult.cpu_model;
        const gpuModel = firstResult.gpu_model;
        const ramGb = firstResult.ram_gb;

        // Calculate averages across ALL runs
        // For efficiency, we calculate the weighted average (Total Energy / Total Tokens)
        // This is more accurate than averaging the per-run ratios
        const totalEnergy = results.reduce((sum, r) => sum + r.energy_wh_net, 0);
        const totalTokens = results.reduce((sum, r) => sum + r.tokens_prompt + r.tokens_completion, 0);

        const avgWhPer1kTokens = totalTokens > 0 ? (totalEnergy / totalTokens) * 1000 : 0;

        // For other metrics, simple average is appropriate or we can sum them
        const avgGCo2 = average(results.map(r => r.g_co2));
        const avgEnergyWhNet = average(results.map(r => r.energy_wh_net));
        const avgDurationS = average(results.map(r => r.duration_s));

        // Calculate tokens per second
        const tokensPerSec = results.map(r => {
            const totalTokens = r.tokens_prompt + r.tokens_completion;
            return totalTokens / r.duration_s;
        });
        const avgTokensPerSecond = average(tokensPerSec);

        stats.push({
            model,
            provider,
            rank: 0, // Will be calculated after sorting
            avgWhPer1kTokens,
            avgGCo2,
            avgEnergyWhNet,
            avgDurationS,
            avgTokensPerSecond,
            totalRuns: results.length,
            region,
            testsets: Array.from(testsets).sort(), // Convert Set to sorted Array
            // Device info
            deviceName,
            deviceType,
            osName,
            osVersion,
            cpuModel,
            gpuModel,
            ramGb,
            // Filtering fields
            isMeasured: isMeasuredData(results),
            device: deviceType,
            results,
        });
    }

    // Sort by efficiency (lower is better) and assign ranks
    stats.sort((a, b) => a.avgWhPer1kTokens - b.avgWhPer1kTokens);
    stats.forEach((stat, index) => {
        stat.rank = index + 1;
    });

    return stats;
}

/**
 * Aggregate benchmark results by model only (cross-hardware average)
 * This creates one entry per model, averaging across all hardware types
 */
export function aggregateByModelOnly(
    benchmarks: { filename: string; results: BenchmarkRun }[]
): ModelStats[] {
    const modelMap = new Map<string, {
        results: BenchmarkResult[];
        filenames: Set<string>;
        testsets: Set<string>;
        deviceTypes: Set<DeviceType>;
    }>();

    // Group results by model + provider only (ignore device)
    for (const { filename, results } of benchmarks) {
        for (const result of results) {
            const deviceType = detectDeviceType(result, filename);
            const key = `${result.model}__${result.provider}`;

            if (!modelMap.has(key)) {
                modelMap.set(key, {
                    results: [],
                    filenames: new Set(),
                    testsets: new Set(),
                    deviceTypes: new Set()
                });
            }

            const group = modelMap.get(key)!;
            group.results.push(result);
            group.filenames.add(filename);
            group.deviceTypes.add(deviceType);

            if (result.testset_name) {
                group.testsets.add(result.testset_name);
            }
        }
    }

    // Calculate aggregated stats for each model
    const stats: ModelStats[] = [];

    for (const [, { results, testsets, deviceTypes }] of modelMap) {
        const firstResult = results[0];
        const model = firstResult.model;
        const provider = firstResult.provider;
        const region = firstResult.region;

        // Calculate weighted average efficiency (Total Energy / Total Tokens)
        const totalEnergy = results.reduce((sum, r) => sum + r.energy_wh_net, 0);
        const totalTokens = results.reduce((sum, r) => sum + r.tokens_prompt + r.tokens_completion, 0);
        const avgWhPer1kTokens = totalTokens > 0 ? (totalEnergy / totalTokens) * 1000 : 0;

        // Other metrics
        const avgGCo2 = average(results.map(r => r.g_co2));
        const avgEnergyWhNet = average(results.map(r => r.energy_wh_net));
        const avgDurationS = average(results.map(r => r.duration_s));

        const tokensPerSec = results.map(r => {
            const totalTok = r.tokens_prompt + r.tokens_completion;
            return totalTok / r.duration_s;
        });
        const avgTokensPerSecond = average(tokensPerSec);

        // For cross-hardware view, show "Multiple" or list of devices
        const deviceTypeArray = Array.from(deviceTypes).sort();
        const deviceName = deviceTypeArray.length > 1 
            ? `${deviceTypeArray.length} devices` 
            : getDeviceDisplayName(deviceTypeArray[0]);

        stats.push({
            model,
            provider,
            rank: 0,
            avgWhPer1kTokens,
            avgGCo2,
            avgEnergyWhNet,
            avgDurationS,
            avgTokensPerSecond,
            totalRuns: results.length,
            region,
            testsets: Array.from(testsets).sort(),
            deviceName,
            deviceType: deviceTypeArray.length === 1 ? deviceTypeArray[0] : 'unknown',
            osName: 'Multiple',
            osVersion: '',
            isMeasured: isMeasuredData(results),
            device: deviceTypeArray.length === 1 ? deviceTypeArray[0] : 'unknown',
            results,
            devicesTested: deviceTypeArray,
        });
    }

    // Sort by efficiency and assign ranks
    stats.sort((a, b) => a.avgWhPer1kTokens - b.avgWhPer1kTokens);
    stats.forEach((stat, index) => {
        stat.rank = index + 1;
    });

    return stats;
}

/**
 * Calculate average of an array of numbers
 */
function average(values: number[]): number {
    if (values.length === 0) return 0;
    return values.reduce((sum, val) => sum + val, 0) / values.length;
}

/**
 * Format Wh value for display
 */
export function formatEnergy(wh: number): string {
    if (wh < 0.001) {
        return `${(wh * 1000000).toFixed(2)} µWh`;
    }
    if (wh < 1) {
        return `${(wh * 1000).toFixed(2)} mWh`;
    }
    return `${wh.toFixed(4)} Wh`;
}

/**
 * Format CO2 value for display
 */
export function formatCO2(grams: number): string {
    if (grams < 0.001) {
        return `${(grams * 1000).toFixed(3)} mg`;
    }
    if (grams < 1) {
        return `${(grams * 1000).toFixed(2)} mg`;
    }
    return `${grams.toFixed(4)} g`;
}

/**
 * Format duration for display
 */
export function formatDuration(seconds: number): string {
    if (seconds < 1) {
        return `${(seconds * 1000).toFixed(0)} ms`;
    }
    return `${seconds.toFixed(2)} s`;
}

/**
 * Format tokens per second
 */
export function formatSpeed(tokensPerSec: number): string {
    return `${tokensPerSec.toFixed(1)} tok/s`;
}

/**
 * Get device display name
 */
export function getDeviceDisplayName(device: DeviceType): string {
    const names: Record<DeviceType, string> = {
        apple: 'Apple Silicon',
        nvidia: 'NVIDIA GPU',
        amd: 'AMD GPU',
        intel: 'Intel CPU',
        unknown: 'Unknown',
    };
    return names[device];
}

/**
 * Get efficiency tier for badge coloring
 */
export function getEfficiencyTier(whPer1kTokens: number): 'excellent' | 'good' | 'fair' | 'poor' {
    if (whPer1kTokens < 0.15) return 'excellent';
    if (whPer1kTokens < 0.35) return 'good';
    if (whPer1kTokens < 0.6) return 'fair';
    return 'poor';
}

/**
 * Get a relatable energy comparison
 * Based on ~20Wh for boiling water for a cup of coffee
 */
export function getEnergyComparison(wh: number): string {
    const coffeeWh = 20; // Approx energy to boil water for a cup of coffee
    const percentage = (wh / coffeeWh) * 100;

    if (percentage < 1) {
        return `Less than 1% of a cup of coffee`;
    }
    return `~${percentage.toFixed(1)}% of a cup of coffee`;
}
