import { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Info, ExternalLink } from 'lucide-react';
import type { ModelStats, FilterState } from '../lib/types';
import { formatEnergy, formatCO2, formatSpeed, getDeviceDisplayName, getEnergyComparison } from '../lib/data-loader';
import { MetricBadge, RankBadge, DeviceBadge, DevicesBadge } from './MetricBadge';

interface LeaderboardTableProps {
    data: ModelStats[];
    filters: FilterState;
    onFilterChange: (filters: Partial<FilterState>) => void;
    onSelectModel: (model: ModelStats) => void;
}

type SortableColumn = 'rank' | 'model' | 'avgWhPer1kTokens' | 'avgGCo2' | 'avgEnergyWhNet' | 'avgTokensPerSecond';

/**
 * Main leaderboard table component with sorting
 */
export function LeaderboardTable({ data, filters, onFilterChange, onSelectModel }: LeaderboardTableProps) {
    const [hoveredRow, setHoveredRow] = useState<string | null>(null);

    // Filter and sort data, then recalculate ranks
    const filteredData = useMemo(() => {
        let result = [...data];

        // Apply search filter
        if (filters.searchQuery) {
            const query = filters.searchQuery.toLowerCase();
            result = result.filter(
                (m) =>
                    m.model.toLowerCase().includes(query) ||
                    m.provider.toLowerCase().includes(query) ||
                    // NEW: Hardware fields
                    m.deviceName.toLowerCase().includes(query) ||
                    (m.gpuModel && m.gpuModel.toLowerCase().includes(query)) ||
                    (m.cpuModel && m.cpuModel.toLowerCase().includes(query))
            );
        }

        // Apply device filter (only in hardware view)
        if (filters.viewMode === 'hardware' && filters.deviceType !== 'all') {
            result = result.filter((m) => m.device === filters.deviceType);
        }

        // Apply method filter
        if (filters.methodFilter === 'measured') {
            result = result.filter((m) => m.isMeasured);
        } else if (filters.methodFilter === 'estimated') {
            result = result.filter((m) => !m.isMeasured);
        }

        // Sort
        result.sort((a, b) => {
            const aVal = a[filters.sortColumn];
            const bVal = b[filters.sortColumn];

            if (typeof aVal === 'string' && typeof bVal === 'string') {
                return filters.sortDirection === 'asc'
                    ? aVal.localeCompare(bVal)
                    : bVal.localeCompare(aVal);
            }

            const numA = Number(aVal) || 0;
            const numB = Number(bVal) || 0;
            return filters.sortDirection === 'asc' ? numA - numB : numB - numA;
        });

        // Recalculate ranks based on filtered & sorted results
        return result.map((item, index) => ({
            ...item,
            rank: index + 1  // Rank is now relative to filtered view
        }));
    }, [data, filters]);

    const handleSort = (column: SortableColumn) => {
        if (filters.sortColumn === column) {
            onFilterChange({
                sortDirection: filters.sortDirection === 'asc' ? 'desc' : 'asc',
            });
        } else {
            onFilterChange({
                sortColumn: column,
                sortDirection: column === 'model' ? 'asc' : 'asc',
            });
        }
    };

    const SortIcon = ({ column }: { column: SortableColumn }) => {
        if (filters.sortColumn !== column) {
            return <ArrowUpDown className="w-4 h-4 text-gray-400" />;
        }
        return filters.sortDirection === 'asc'
            ? <ArrowUp className="w-4 h-4 text-eco-500" />
            : <ArrowDown className="w-4 h-4 text-eco-500" />;
    };

    const columns = [
        { key: 'rank' as const, label: 'Rank', sortable: true, className: 'w-16' },
        { key: 'model' as const, label: 'Model', sortable: true, className: 'min-w-[200px]' },
        { key: 'avgWhPer1kTokens' as const, label: 'Efficiency', sortable: true, info: 'Watt-hours per 1000 tokens (lower is better)' },
        { key: 'avgGCo2' as const, label: 'CO₂', sortable: true, info: 'Grams of CO₂ emissions' },
        { key: 'avgEnergyWhNet' as const, label: 'Energy', sortable: true, info: 'Net energy consumption in Wh' },
        { key: 'avgTokensPerSecond' as const, label: 'Speed', sortable: true, info: 'Tokens generated per second' },
        { key: 'device', label: filters.viewMode === 'models' ? 'Devices Tested' : 'Device', sortable: false },
        { key: 'method', label: 'Method', sortable: false },
    ];

    if (filteredData.length === 0) {
        return (
            <div className="card p-12 text-center">
                <p className="text-gray-500 dark:text-gray-400">
                    No models found matching your filters.
                </p>
            </div>
        );
    }

    return (
        <div className="card overflow-hidden">
            {/* Desktop Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead className="bg-gray-50 dark:bg-dark-border/50">
                        <tr>
                            {columns.map((col) => (
                                <th
                                    key={col.key}
                                    className={`px-4 py-3 table-header ${col.className || ''} ${col.sortable ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-dark-border transition-colors' : ''
                                        }`}
                                    onClick={() => col.sortable && handleSort(col.key as SortableColumn)}
                                >
                                    <div className="flex items-center gap-2">
                                        <span>{col.label}</span>
                                        {col.info && (
                                            <span className="group relative z-10" title={col.info}>
                                                <Info className="w-3.5 h-3.5 text-gray-400 cursor-help" />
                                            </span>
                                        )}
                                        {col.sortable && <SortIcon column={col.key as SortableColumn} />}
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {filteredData.map((model, index) => (
                            <tr
                                key={`${model.model}-${index}`}
                                className={`table-row cursor-pointer ${hoveredRow === model.model ? 'bg-eco-50 dark:bg-eco-900/10' : ''
                                    }`}
                                onMouseEnter={() => setHoveredRow(model.model)}
                                onMouseLeave={() => setHoveredRow(null)}
                                onClick={() => onSelectModel(model)}
                                style={{ animationDelay: `${index * 50}ms` }}
                            >
                                <td className="table-cell">
                                    <RankBadge rank={model.rank} />
                                </td>
                                <td className="table-cell">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-gray-900 dark:text-white">
                                            {model.model}
                                        </span>
                                        <span className="text-xs text-gray-500 dark:text-gray-400">
                                            {model.provider} • {model.totalRuns} runs
                                        </span>
                                        {model.testsets && model.testsets.length > 0 && (
                                            <div className="flex flex-wrap gap-1 mt-1">
                                                {model.testsets.map((ts, i) => (
                                                    <span key={i} className="text-[10px] px-1.5 py-0.5 bg-gray-100 dark:bg-dark-border rounded text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-dark-border/50">
                                                        {ts.replace(/ \(.*\)/, '')}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </td>
                                <td className="table-cell">
                                    <div className="flex items-center gap-2">
                                        <span className="font-mono font-medium">
                                            {model.avgWhPer1kTokens.toFixed(3)}
                                        </span>
                                        <span className="text-xs text-gray-500">Wh/1k</span>
                                        <MetricBadge value={model.avgWhPer1kTokens} type="efficiency" showIcon={false} />
                                    </div>
                                </td>
                                <td className="table-cell font-mono">
                                    {formatCO2(model.avgGCo2)}
                                </td>
                                <td className="table-cell">
                                    <div className="flex flex-col">
                                        <span className="font-mono">{formatEnergy(model.avgEnergyWhNet)}</span>
                                        <span className="text-[10px] text-gray-500">
                                            {getEnergyComparison(model.avgEnergyWhNet)}
                                        </span>
                                    </div>
                                </td>
                                <td className="table-cell font-mono">
                                    {formatSpeed(model.avgTokensPerSecond)}
                                </td>
                                <td className="table-cell">
                                    {filters.viewMode === 'models' ? (
                                        model.devicesTested ? (
                                            <DevicesBadge devices={model.devicesTested} />
                                        ) : (
                                            <DeviceBadge device={getDeviceDisplayName(model.device)} />
                                        )
                                    ) : (
                                        <div className="flex flex-col items-start gap-0.5">
                                            <DeviceBadge device={getDeviceDisplayName(model.device)} />
                                            <span
                                                className="text-[10px] text-gray-500 dark:text-gray-400 font-mono truncate max-w-[150px]"
                                                title={model.gpuModel || model.cpuModel || model.deviceName}
                                            >
                                                {model.gpuModel || model.cpuModel || model.deviceName}
                                            </span>
                                        </div>
                                    )}
                                </td>
                                <td className="table-cell">
                                    <MetricBadge
                                        value={0}
                                        type={model.isMeasured ? 'measured' : 'estimated'}
                                    />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Mobile Cards (shown on small screens) */}
            <div className="md:hidden divide-y divide-gray-100 dark:divide-dark-border">
                {filteredData.map((model, index) => (
                    <div
                        key={`mobile-${model.model}-${index}`}
                        className="p-4 hover:bg-gray-50 dark:hover:bg-dark-border/50 transition-colors cursor-pointer"
                        onClick={() => onSelectModel(model)}
                    >
                        <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-3">
                                <RankBadge rank={model.rank} />
                                <div>
                                    <h3 className="font-medium text-gray-900 dark:text-white">
                                        {model.model}
                                    </h3>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                        {model.provider}
                                    </p>
                                </div>
                            </div>
                            <MetricBadge
                                value={0}
                                type={model.isMeasured ? 'measured' : 'estimated'}
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                                <span className="text-gray-500 dark:text-gray-400">Efficiency:</span>
                                <span className="ml-1 font-mono font-medium">
                                    {model.avgWhPer1kTokens.toFixed(3)} Wh/1k
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-500 dark:text-gray-400">CO₂:</span>
                                <span className="ml-1 font-mono">
                                    {formatCO2(model.avgGCo2)}
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-500 dark:text-gray-400">Speed:</span>
                                <span className="ml-1 font-mono">
                                    {formatSpeed(model.avgTokensPerSecond)}
                                </span>
                            </div>
                            <div>
                                {filters.viewMode === 'models' ? (
                                    model.devicesTested ? (
                                        <DevicesBadge devices={model.devicesTested} />
                                    ) : (
                                        <DeviceBadge device={getDeviceDisplayName(model.device)} />
                                    )
                                ) : (
                                    <div className="flex flex-col items-start gap-0.5">
                                        <DeviceBadge device={getDeviceDisplayName(model.device)} />
                                        <span
                                            className="text-[10px] text-gray-500 dark:text-gray-400 font-mono truncate max-w-[150px]"
                                            title={model.gpuModel || model.cpuModel || model.deviceName}
                                        >
                                            {model.gpuModel || model.cpuModel || model.deviceName}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 bg-gray-50 dark:bg-dark-border/50 border-t border-gray-100 dark:border-dark-border">
                <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                    <span>
                        Showing {filteredData.length} of {data.length} models
                    </span>
                    <a
                        href="https://github.com/NOVADEDOG/energy-leaderboard-runner"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 hover:text-eco-500 transition-colors"
                    >
                        <span>Contribute data</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                </div>
            </div>
        </div>
    );
}
