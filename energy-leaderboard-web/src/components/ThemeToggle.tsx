import { Sun, Moon, Laptop } from 'lucide-react';
import type { ThemeMode } from '../lib/types';

interface ThemeToggleProps {
    theme: ThemeMode;
    onChange: (theme: ThemeMode) => void;
}

/**
 * Theme toggle button for switching between light/dark/system modes
 */
export function ThemeToggle({ theme, onChange }: ThemeToggleProps) {
    const modes: { value: ThemeMode; icon: React.ReactNode; label: string }[] = [
        { value: 'light', icon: <Sun className="w-4 h-4" />, label: 'Light' },
        { value: 'dark', icon: <Moon className="w-4 h-4" />, label: 'Dark' },
        { value: 'system', icon: <Laptop className="w-4 h-4" />, label: 'System' },
    ];

    const currentIndex = modes.findIndex((m) => m.value === theme);
    const nextMode = modes[(currentIndex + 1) % modes.length];

    return (
        <button
            onClick={() => onChange(nextMode.value)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-border transition-colors"
            title={`Switch to ${nextMode.label} mode`}
        >
            {modes[currentIndex].icon}
        </button>
    );
}
