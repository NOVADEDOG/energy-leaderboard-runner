import { Search, Filter, ChevronDown, LayoutGrid, Cpu } from 'lucide-react';
import type { FilterState, DeviceType } from '../lib/types';

interface FilterBarProps {
    filters: FilterState;
    onFilterChange: (filters: Partial<FilterState>) => void;
}

/**
 * Filter bar with view toggle, search, device type filter, and method filter
 */
export function FilterBar({ filters, onFilterChange }: FilterBarProps) {
    const deviceOptions: { value: DeviceType | 'all'; label: string }[] = [
        { value: 'all', label: 'All Devices' },
        { value: 'apple', label: 'Apple Silicon' },
        { value: 'nvidia', label: 'NVIDIA GPU' },
        { value: 'amd', label: 'AMD GPU' },
        { value: 'intel', label: 'Intel CPU' },
    ];

    const methodOptions = [
        { value: 'all', label: 'All Methods' },
        { value: 'measured', label: 'Measured Only' },
        { value: 'estimated', label: 'Estimated Only' },
    ];

    return (
        <div className="card p-4 mb-6">
            {/* View Toggle */}
            <div className="flex gap-2 mb-4 pb-4 border-b border-gray-200 dark:border-dark-border">
                <button
                    onClick={() => onFilterChange({ viewMode: 'models' })}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${filters.viewMode === 'models'
                            ? 'bg-eco-500 text-white'
                            : 'bg-gray-100 dark:bg-dark-border text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-border/70'
                        }`}
                >
                    <LayoutGrid className="w-4 h-4" />
                    <span>Models</span>
                    <span className="text-xs opacity-75">(Cross-Hardware Avg)</span>
                </button>
                <button
                    onClick={() => onFilterChange({ viewMode: 'hardware' })}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${filters.viewMode === 'hardware'
                            ? 'bg-eco-500 text-white'
                            : 'bg-gray-100 dark:bg-dark-border text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-border/70'
                        }`}
                >
                    <Cpu className="w-4 h-4" />
                    <span>Hardware Details</span>
                    <span className="text-xs opacity-75">(Per Device)</span>
                </button>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
                {/* Search Input */}
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search models..."
                        value={filters.searchQuery}
                        onChange={(e) => onFilterChange({ searchQuery: e.target.value })}
                        className="input pl-10"
                    />
                </div>

                {/* Device Type Filter - only show in hardware view */}
                {filters.viewMode === 'hardware' && (
                    <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                        <select
                            value={filters.deviceType}
                            onChange={(e) => onFilterChange({ deviceType: e.target.value as DeviceType | 'all' })}
                            className="select pl-9 min-w-[160px]"
                        >
                            {deviceOptions.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                    </div>
                )}

                {/* Method Filter */}
                <div className="relative">
                    <select
                        value={filters.methodFilter}
                        onChange={(e) => onFilterChange({ methodFilter: e.target.value as FilterState['methodFilter'] })}
                        className="select min-w-[150px]"
                    >
                        {methodOptions.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                </div>
            </div>
        </div>
    );
}
