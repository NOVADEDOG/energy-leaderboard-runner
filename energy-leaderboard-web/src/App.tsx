import { useState, useEffect, useMemo } from 'react';
import { Leaf, Github, ExternalLink, Zap, Coffee, Cloud } from 'lucide-react';
import { loadAllBenchmarks, aggregateByModel, aggregateByModelOnly } from './lib/data-loader';
import type { ModelStats, FilterState, ThemeMode } from './lib/types';
import { FilterBar } from './components/FilterBar';
import { LeaderboardTable } from './components/LeaderboardTable';
import { DetailModal } from './components/DetailModal';
import { ThemeToggle } from './components/ThemeToggle';

function App() {
    // Data state - store both aggregation types
    const [dataByHardware, setDataByHardware] = useState<ModelStats[]>([]);
    const [dataByModel, setDataByModel] = useState<ModelStats[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // UI state
    const [selectedModel, setSelectedModel] = useState<ModelStats | null>(null);
    const [theme, setTheme] = useState<ThemeMode>(() => {
        if (typeof window !== 'undefined') {
            return (localStorage.getItem('theme') as ThemeMode) || 'system';
        }
        return 'system';
    });

    // Filter state
    const [filters, setFilters] = useState<FilterState>({
        searchQuery: '',
        deviceType: 'all',
        methodFilter: 'all',
        sortColumn: 'avgWhPer1kTokens',
        sortDirection: 'asc',
        viewMode: 'models', // Default to cross-hardware model view
    });

    // Get the appropriate data based on view mode
    const data = filters.viewMode === 'models' ? dataByModel : dataByHardware;

    // Load benchmark data on mount
    useEffect(() => {
        async function loadData() {
            try {
                setLoading(true);
                const benchmarks = await loadAllBenchmarks();
                const aggregatedByHardware = aggregateByModel(benchmarks);
                const aggregatedByModel = aggregateByModelOnly(benchmarks);
                setDataByHardware(aggregatedByHardware);
                setDataByModel(aggregatedByModel);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load data');
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    // Theme handling
    useEffect(() => {
        const root = document.documentElement;

        if (theme === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            root.classList.toggle('dark', prefersDark);
        } else {
            root.classList.toggle('dark', theme === 'dark');
        }

        localStorage.setItem('theme', theme);
    }, [theme]);

    // Listen for system theme changes
    useEffect(() => {
        if (theme !== 'system') return;

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handler = (e: MediaQueryListEvent) => {
            document.documentElement.classList.toggle('dark', e.matches);
        };

        mediaQuery.addEventListener('change', handler);
        return () => mediaQuery.removeEventListener('change', handler);
    }, [theme]);

    // Calculate summary stats - total impact of all testing
    const summaryStats = useMemo(() => {
        if (dataByHardware.length === 0) return null;

        // Use hardware data for totals (to avoid double counting in model view)
        const allResults = dataByHardware.flatMap(m => m.results);

        const totalRuns = allResults.length;
        const totalEnergyWh = allResults.reduce((sum, r) => sum + r.energy_wh_net, 0);
        const totalCO2g = allResults.reduce((sum, r) => sum + r.g_co2, 0);
        const totalTokens = allResults.reduce((sum, r) => sum + r.tokens_prompt + r.tokens_completion, 0);

        // Coffee cup equivalent: ~20Wh to boil water for a cup
        const coffeeCups = totalEnergyWh / 20;

        const bestModel = data[0]; // Best in current view

        return {
            totalRuns,
            totalEnergyWh,
            totalCO2g,
            totalTokens,
            coffeeCups,
            bestModel,
            modelCount: data.length
        };
    }, [data, dataByHardware]);

    const handleFilterChange = (updates: Partial<FilterState>) => {
        setFilters((prev) => ({ ...prev, ...updates }));
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <Leaf className="w-12 h-12 text-eco-500 mx-auto animate-pulse-eco" />
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Loading benchmark data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center max-w-md">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                        Failed to Load Data
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="btn-primary"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
            {/* Header */}
            <header className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-eco-500/10 rounded-lg">
                                <Leaf className="w-6 h-6 text-eco-500" />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold text-gray-900 dark:text-white">
                                    Energy Leaderboard
                                </h1>
                                <p className="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">
                                    Sustainable AI Benchmarks
                                </p>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                            <ThemeToggle theme={theme} onChange={setTheme} />
                            <a
                                href="https://github.com/NOVADEDOG/energy-leaderboard-runner"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border transition-colors"
                                title="View on GitHub"
                            >
                                <Github className="w-5 h-5" />
                            </a>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Hero Section */}
                <div className="mb-8">
                    <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Compare LLM Energy Efficiency
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
                        Real-world energy measurements from local LLM benchmarks.
                        Lower Wh/1k tokens = more efficient. All data is measured from actual hardware.
                    </p>
                </div>

                {/* Summary Stats - Total Impact */}
                {summaryStats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        <StatCard
                            icon={<Zap className="w-5 h-5 text-yellow-500" />}
                            label="Total Energy Used"
                            value={summaryStats.totalEnergyWh < 1
                                ? `${(summaryStats.totalEnergyWh * 1000).toFixed(1)} mWh`
                                : `${summaryStats.totalEnergyWh.toFixed(2)} Wh`}
                        />
                        <StatCard
                            icon={<Coffee className="w-5 h-5 text-amber-600" />}
                            label="Coffee Cups ☕"
                            value={summaryStats.coffeeCups < 0.01
                                ? `${(summaryStats.coffeeCups * 100).toFixed(2)}%`
                                : summaryStats.coffeeCups < 1
                                    ? `${(summaryStats.coffeeCups * 100).toFixed(1)}% of a cup`
                                    : `${summaryStats.coffeeCups.toFixed(1)} cups`}
                            subtext="Energy to boil water"
                        />
                        <StatCard
                            icon={<Cloud className="w-5 h-5 text-gray-500" />}
                            label="CO₂ Emissions"
                            value={summaryStats.totalCO2g < 1
                                ? `${(summaryStats.totalCO2g * 1000).toFixed(1)} mg`
                                : `${summaryStats.totalCO2g.toFixed(2)} g`}
                        />
                        <StatCard
                            icon={<Leaf className="w-5 h-5 text-green-500" />}
                            label="Most Efficient"
                            value={summaryStats.bestModel?.model || 'N/A'}
                            subtext={`${summaryStats.totalRuns} total runs`}
                        />
                    </div>
                )}

                {/* Filters */}
                <FilterBar filters={filters} onFilterChange={handleFilterChange} />

                {/* Leaderboard Table */}
                <LeaderboardTable
                    data={data}
                    filters={filters}
                    onFilterChange={handleFilterChange}
                    onSelectModel={setSelectedModel}
                />

                {/* Info Section */}
                <div className="mt-8 card p-6">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
                        About This Leaderboard
                    </h3>
                    <div className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
                        <p>
                            <strong>Wh/1k tokens</strong> measures watt-hours of energy consumed per 1000 tokens generated.
                            Lower values indicate more energy-efficient models.
                        </p>
                        <p>
                            <strong>Measured</strong> data comes from real hardware sensors (powermetrics, NVML, RAPL).
                            <strong>Estimated</strong> data uses power draw approximations.
                        </p>
                        <p>
                            Want to contribute your own benchmark results?{' '}
                            <a
                                href="https://github.com/NOVADEDOG/energy-leaderboard-runner"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-eco-600 dark:text-eco-400 hover:underline inline-flex items-center gap-1"
                            >
                                Run the benchmark tool
                                <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                        </p>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-gray-200 dark:border-dark-border mt-12">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                            <Leaf className="w-4 h-4 text-eco-500" />
                            <span>Energy Leaderboard — Open source AI sustainability benchmarks</span>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                            <a
                                href="https://github.com/NOVADEDOG/energy-leaderboard-runner"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-gray-500 dark:text-gray-400 hover:text-eco-500 transition-colors"
                            >
                                GitHub
                            </a>
                            <a
                                href="https://github.com/NOVADEDOG/energy-leaderboard-runner/blob/main/LICENSE"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-gray-500 dark:text-gray-400 hover:text-eco-500 transition-colors"
                            >
                                MIT License
                            </a>
                        </div>
                    </div>
                </div>
            </footer>

            {/* Detail Modal */}
            <DetailModal model={selectedModel} onClose={() => setSelectedModel(null)} />
        </div>
    );
}

interface StatCardProps {
    icon: React.ReactNode;
    label: string;
    value: string;
    subtext?: string;
}

function StatCard({ icon, label, value, subtext }: StatCardProps) {
    return (
        <div className="card p-4">
            <div className="flex items-center gap-2 mb-1">
                {icon}
                <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
            </div>
            <p className="text-lg font-bold text-gray-900 dark:text-white truncate">{value}</p>
            {subtext && (
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{subtext}</p>
            )}
        </div>
    );
}

export default App;
