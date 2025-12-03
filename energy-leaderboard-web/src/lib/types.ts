/**
 * TypeScript interfaces matching the Runner's JSON output schema
 * @see /src/data/metrics_schema.json
 */

/** A single measurement result from a benchmark run */
export interface BenchmarkResult {
    // Required fields
    tokens_prompt: number;
    tokens_completion: number;
    duration_s: number;
    response_time_s: number;
    energy_wh_raw: number;
    energy_wh_net: number;
    wh_per_1k_tokens: number;
    energy_kwh_per_token: number;
    g_co2: number;
    provider: string;
    model: string;
    region: string;
    notice: string | null;
    sampling_ms: number;

    // Device information (mandatory in new schema)
    device_name: string;
    device_type: 'apple' | 'nvidia' | 'amd' | 'intel' | 'unknown';
    os_name: string;
    os_version: string;

    // Optional device fields
    cpu_model?: string;
    gpu_model?: string;
    ram_gb?: number;
    chip_architecture?: string;

    // Optional prompt/completion fields
    prompt?: string;
    completion?: string;
    testset_id?: string;
    testset_name?: string;
    testset_goal?: string;
    testset_notes?: string;
    question_id?: string;
    question_difficulty?: string;
    question_task_type?: string;
    expected_answer_description?: string;
    max_output_tokens_hint?: number;
    energy_relevance?: string;
    tags?: string[];
}

/** A complete benchmark run file (array of results) */
export type BenchmarkRun = BenchmarkResult[];

/** Metadata about a loaded benchmark file */
export interface BenchmarkFile {
    filename: string;
    results: BenchmarkRun;
    loadedAt: Date;
}

/** Aggregated stats for a model across all runs */
export interface ModelStats {
    model: string;
    provider: string;
    rank: number;

    // Aggregated metrics (averages)
    avgWhPer1kTokens: number;
    avgGCo2: number;
    avgEnergyWhNet: number;
    avgDurationS: number;
    avgTokensPerSecond: number;

    // Run metadata
    totalRuns: number;
    region: string;
    testsetName?: string; // Deprecated: use testsets instead
    testsets: string[]; // List of datasets included in this average

    // Device information
    deviceName: string;
    deviceType: DeviceType;
    osName: string;
    osVersion: string;
    cpuModel?: string;
    gpuModel?: string;
    ramGb?: number;

    // For sorting/filtering
    isMeasured: boolean; // true if has real power data, false if estimated
    device: DeviceType;  // Alias for deviceType for backward compat

    // Raw results for detail view
    results: BenchmarkResult[];

    // For cross-hardware view: list of unique devices tested
    devicesTested?: DeviceType[];
}

/** Device/hardware categories for filtering */
export type DeviceType = 'apple' | 'nvidia' | 'amd' | 'intel' | 'unknown';

/** View mode for the leaderboard */
export type ViewMode = 'models' | 'hardware';

/** Filter state for the leaderboard */
export interface FilterState {
    searchQuery: string;
    deviceType: DeviceType | 'all';
    methodFilter: 'all' | 'measured' | 'estimated';
    sortColumn: keyof ModelStats;
    sortDirection: 'asc' | 'desc';
    viewMode: ViewMode;
}

/** Theme state */
export type ThemeMode = 'light' | 'dark' | 'system';
