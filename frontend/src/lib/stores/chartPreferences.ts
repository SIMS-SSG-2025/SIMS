import { writable } from 'svelte/store';
import type { TimeRangeOption, TimeRange } from '$lib/api/stats';

export interface ChartPreferences {
    selectedRange: TimeRangeOption;
    customTimeRange: TimeRange | null;
    showPersons: boolean;
    showVehicles: boolean;
    showPPEBreaches: boolean;
    showZoneEntries: boolean;
    chartType: 'bar' | 'line';
}

const defaultPreferences: ChartPreferences = {
    selectedRange: 'day',
    customTimeRange: null,
    showPersons: true,
    showVehicles: true,
    showPPEBreaches: true,
    showZoneEntries: true,
    chartType: 'bar'
};

export const chartPreferences = writable<ChartPreferences>(defaultPreferences);
