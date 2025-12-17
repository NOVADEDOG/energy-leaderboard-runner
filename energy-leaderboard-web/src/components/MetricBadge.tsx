import { getEfficiencyTier } from '../lib/data-loader';
import { Leaf, AlertTriangle, Gauge, Zap } from 'lucide-react';
import type { DeviceType } from '../lib/types';

interface MetricBadgeProps {
    value: number;
    type: 'efficiency' | 'measured' | 'estimated';
    showIcon?: boolean;
}

/**
 * Badge component for displaying metric status
 * Shows efficiency tier with green leaf icons or warning for estimated data
 */
export function MetricBadge({ value, type, showIcon = true }: MetricBadgeProps) {
    if (type === 'measured') {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-eco-100 dark:bg-eco-900/30 text-eco-700 dark:text-eco-400">
                {showIcon && <Gauge className="w-3 h-3" />}
                Measured
            </span>
        );
    }

    if (type === 'estimated') {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                {showIcon && <AlertTriangle className="w-3 h-3" />}
                Estimated
            </span>
        );
    }

    // Efficiency badge
    const tier = getEfficiencyTier(value);
    const tierStyles = {
        excellent: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
        good: 'bg-eco-100 dark:bg-eco-900/30 text-eco-700 dark:text-eco-400',
        fair: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
        poor: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
    };

    const tierLabels = {
        excellent: 'Excellent',
        good: 'Good',
        fair: 'Fair',
        poor: 'High Use',
    };

    const TierIcon = tier === 'excellent' || tier === 'good' ? Leaf : Zap;

    return (
        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${tierStyles[tier]}`}>
            {showIcon && <TierIcon className="w-3 h-3" />}
            {tierLabels[tier]}
        </span>
    );
}

interface RankBadgeProps {
    rank: number;
}

/**
 * Badge showing the model's rank in the leaderboard
 */
export function RankBadge({ rank }: RankBadgeProps) {
    const getRankStyle = () => {
        if (rank === 1) return 'bg-gradient-to-br from-yellow-400 to-amber-500 text-white shadow-lg shadow-amber-200 dark:shadow-amber-900/50';
        if (rank === 2) return 'bg-gradient-to-br from-gray-300 to-gray-400 text-gray-800';
        if (rank === 3) return 'bg-gradient-to-br from-amber-600 to-amber-700 text-white';
        return 'bg-gray-100 dark:bg-dark-border text-gray-600 dark:text-gray-400';
    };

    return (
        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${getRankStyle()}`}>
            {rank}
        </span>
    );
}

interface DeviceBadgeProps {
    device: string;
}

/**
 * Badge showing the device/hardware type
 */
export function DeviceBadge({ device }: DeviceBadgeProps) {
    const deviceStyles: Record<string, string> = {
        'Apple Silicon': 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-800',
        'NVIDIA GPU': 'bg-green-600 text-white',
        'AMD GPU': 'bg-red-600 text-white',
        'Intel CPU': 'bg-blue-600 text-white',
        'Unknown': 'bg-gray-400 text-white',
    };

    return (
        <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${deviceStyles[device] || deviceStyles['Unknown']}`}>
            {device}
        </span>
    );
}

interface DevicesBadgeProps {
    devices: DeviceType[];
}

/**
 * Badge showing multiple devices tested (for cross-hardware view)
 */
export function DevicesBadge({ devices }: DevicesBadgeProps) {
    const deviceColors: Record<DeviceType, string> = {
        'apple': 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-800',
        'nvidia': 'bg-green-600 text-white',
        'amd': 'bg-red-600 text-white',
        'intel': 'bg-blue-600 text-white',
        'unknown': 'bg-gray-400 text-white',
    };

    const deviceLabels: Record<DeviceType, string> = {
        'apple': 'Apple',
        'nvidia': 'NVIDIA',
        'amd': 'AMD',
        'intel': 'Intel',
        'unknown': '?',
    };

    return (
        <div className="flex flex-wrap gap-1">
            {devices.map((device) => (
                <span 
                    key={device}
                    className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${deviceColors[device]}`}
                    title={device}
                >
                    {deviceLabels[device]}
                </span>
            ))}
        </div>
    );
}
