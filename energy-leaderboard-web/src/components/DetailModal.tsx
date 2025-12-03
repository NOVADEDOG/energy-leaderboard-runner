import { X, Zap, Clock, Cpu, MapPin, FileText, Monitor } from 'lucide-react';
import type { ModelStats } from '../lib/types';
import { formatEnergy, formatCO2, formatDuration, formatSpeed, getDeviceDisplayName } from '../lib/data-loader';
import { MetricBadge, DeviceBadge } from './MetricBadge';

interface DetailModalProps {
    model: ModelStats | null;
    onClose: () => void;
}

/**
 * Modal showing detailed information about a model's benchmark results
 */
export function DetailModal({ model, onClose }: DetailModalProps) {
    if (!model) return null;

    // Calculate additional stats
    const totalTokens = model.results.reduce(
        (sum, r) => sum + r.tokens_prompt + r.tokens_completion,
        0
    );
    const avgPromptTokens = Math.round(
        model.results.reduce((sum, r) => sum + r.tokens_prompt, 0) / model.results.length
    );
    const avgCompletionTokens = Math.round(
        model.results.reduce((sum, r) => sum + r.tokens_completion, 0) / model.results.length
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white dark:bg-dark-surface rounded-2xl shadow-2xl animate-fadeIn">
                {/* Header */}
                <div className="sticky top-0 bg-white dark:bg-dark-surface border-b border-gray-100 dark:border-dark-border px-6 py-4 flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                            {model.model}
                        </h2>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            {model.provider} • {model.totalRuns} benchmark runs
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-dark-border rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                    {/* Status Badges */}
                    <div className="flex flex-wrap gap-2">
                        <MetricBadge value={model.avgWhPer1kTokens} type="efficiency" />
                        <MetricBadge value={0} type={model.isMeasured ? 'measured' : 'estimated'} />
                        <DeviceBadge device={getDeviceDisplayName(model.device)} />
                    </div>

                    {/* Key Metrics Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <MetricCard
                            icon={<Zap className="w-5 h-5 text-eco-500" />}
                            label="Efficiency"
                            value={`${model.avgWhPer1kTokens.toFixed(3)} Wh/1k`}
                            subtext="per 1000 tokens"
                        />
                        <MetricCard
                            icon={<Cpu className="w-5 h-5 text-blue-500" />}
                            label="Avg Energy"
                            value={formatEnergy(model.avgEnergyWhNet)}
                            subtext="per request"
                        />
                        <MetricCard
                            icon={<Clock className="w-5 h-5 text-purple-500" />}
                            label="Speed"
                            value={formatSpeed(model.avgTokensPerSecond)}
                            subtext="generation rate"
                        />
                        <MetricCard
                            icon={<MapPin className="w-5 h-5 text-amber-500" />}
                            label="CO₂ Emissions"
                            value={formatCO2(model.avgGCo2)}
                            subtext={`region: ${model.region}`}
                        />
                    </div>

                    {/* Token Stats */}
                    <div className="card p-4">
                        <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            Token Statistics
                        </h3>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                                <p className="text-gray-500 dark:text-gray-400">Total Tokens</p>
                                <p className="font-mono font-medium">{totalTokens.toLocaleString()}</p>
                            </div>
                            <div>
                                <p className="text-gray-500 dark:text-gray-400">Avg Prompt</p>
                                <p className="font-mono font-medium">{avgPromptTokens}</p>
                            </div>
                            <div>
                                <p className="text-gray-500 dark:text-gray-400">Avg Completion</p>
                                <p className="font-mono font-medium">{avgCompletionTokens}</p>
                            </div>
                        </div>
                    </div>

                    {/* Testset Info */}
                    {model.testsetName && (
                        <div className="card p-4">
                            <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                                Testset Information
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-300">
                                {model.testsetName}
                            </p>
                        </div>
                    )}

                    {/* Device Information */}
                    <div className="card p-4">
                        <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                            <Monitor className="w-4 h-4" />
                            Device Information
                        </h3>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p className="text-gray-500 dark:text-gray-400">Device</p>
                                <p className="font-medium">{model.deviceName}</p>
                            </div>
                            <div>
                                <p className="text-gray-500 dark:text-gray-400">Operating System</p>
                                <p className="font-medium">{model.osName} {model.osVersion}</p>
                            </div>
                            {model.cpuModel && (
                                <div>
                                    <p className="text-gray-500 dark:text-gray-400">CPU</p>
                                    <p className="font-medium text-xs">{model.cpuModel}</p>
                                </div>
                            )}
                            {model.gpuModel && (
                                <div>
                                    <p className="text-gray-500 dark:text-gray-400">GPU</p>
                                    <p className="font-medium text-xs">{model.gpuModel}</p>
                                </div>
                            )}
                            {model.ramGb && (
                                <div>
                                    <p className="text-gray-500 dark:text-gray-400">RAM</p>
                                    <p className="font-medium">{model.ramGb} GB</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Sample Results */}
                    <div>
                        <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                            Sample Results ({Math.min(3, model.results.length)} of {model.results.length})
                        </h3>
                        <div className="space-y-3">
                            {model.results.slice(0, 3).map((result, idx) => (
                                <div key={idx} className="card p-4 text-sm">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="font-medium text-gray-700 dark:text-gray-200">
                                            {result.question_id || `Run ${idx + 1}`}
                                        </span>
                                        <span className="text-xs text-gray-500">
                                            {formatDuration(result.duration_s)}
                                        </span>
                                    </div>
                                    {result.prompt && (
                                        <p className="text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                                            <span className="font-medium">Prompt:</span> {result.prompt}
                                        </p>
                                    )}
                                    <div className="flex gap-4 text-xs text-gray-500">
                                        <span>Energy: {formatEnergy(result.energy_wh_net)}</span>
                                        <span>Tokens: {result.tokens_prompt + result.tokens_completion}</span>
                                        <span>CO₂: {formatCO2(result.g_co2)}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="sticky bottom-0 bg-white dark:bg-dark-surface border-t border-gray-100 dark:border-dark-border px-6 py-4">
                    <button
                        onClick={onClose}
                        className="w-full btn-secondary"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}

interface MetricCardProps {
    icon: React.ReactNode;
    label: string;
    value: string;
    subtext?: string;
}

function MetricCard({ icon, label, value, subtext }: MetricCardProps) {
    return (
        <div className="card p-4">
            <div className="flex items-center gap-2 mb-2">
                {icon}
                <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
            </div>
            <p className="text-lg font-bold text-gray-900 dark:text-white">{value}</p>
            {subtext && (
                <p className="text-xs text-gray-500 dark:text-gray-400">{subtext}</p>
            )}
        </div>
    );
}
