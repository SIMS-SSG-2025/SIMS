<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { Chart, Title, Tooltip, Legend, BarElement, LineElement, PointElement, CategoryScale, LinearScale, BarController, LineController, Filler } from 'chart.js';
    import { X, BarChart3, LineChart } from 'lucide-svelte';
    import type { TimeRangeOption, TimeRange } from '$lib/api/stats';
    import {
        calculateTimeRange,
        getMockChartModalData,
        fetchEventsForLocation,
        createChartDataFromEvents,
        calculatePPEComplianceFromEvents,
        findEarliestEventTime,
        type Event
    } from '$lib/api/stats';
    import { chartPreferences } from '$lib/stores/chartPreferences';
    import DateRangePicker from './DateRangePicker.svelte';

    // ============================================
    // DATA SOURCE CONFIGURATION
    // ============================================
    // Set this to false to use mock data for charts
    const USE_REAL_DATA = false;

    Chart.register(
        Title, Tooltip, Legend,
        BarElement, LineElement, PointElement,
        CategoryScale, LinearScale,
        BarController, LineController,
        Filler
    );

    type ChartModalProps = {
        open: boolean;
        onClose: () => void;
        chartType: 'bar' | 'line';
        initialTitle?: string;
        locationId?: number;
    };

    let {
        open = $bindable(false),
        onClose,
        chartType = 'bar',
        initialTitle = 'Chart Details',
        locationId
    }: ChartModalProps = $props();

    // Auto-subscribe to global store using Svelte 5 rune
    let preferences = $derived($chartPreferences);

    // Local state synced with store
    let showPersons = $state($chartPreferences.showPersons);
    let showVehicles = $state($chartPreferences.showVehicles);
    let showPPEBreaches = $state($chartPreferences.showPPEBreaches);
    let showZoneEntries = $state($chartPreferences.showZoneEntries);
    let selectedRange = $state<TimeRangeOption>($chartPreferences.selectedRange);
    let customTimeRange = $state<TimeRange | null>($chartPreferences.customTimeRange);
    let currentChartType = $state<'bar' | 'line'>($chartPreferences.chartType);

    // Sync local state when store changes
    $effect(() => {
        showPersons = preferences.showPersons;
        showVehicles = preferences.showVehicles;
        showPPEBreaches = preferences.showPPEBreaches;
        showZoneEntries = preferences.showZoneEntries;
        selectedRange = preferences.selectedRange;
        customTimeRange = preferences.customTimeRange;
        currentChartType = preferences.chartType;
    });

    let showCustomDatePicker = $state(false);

    // Track previous chart type to detect actual changes
    let prevChartType = $state<'bar' | 'line' | null>(null);

    // Chart data
    let chartLabels = $state<string[]>([]);
    let personsData = $state<number[]>([]);
    let vehiclesData = $state<number[]>([]);
    let ppeBreachesData = $state<number[]>([]);
    let zoneEntriesData = $state<number[]>([]);
    let earliestEventTime = $state<Date | null>(null); // Store earliest event for "All" time range

    let canvasElement = $state<HTMLCanvasElement | undefined>(undefined);
    let chart: Chart | null = null;
    let loading = $state(false);

    // Event cache to avoid re-fetching data when switching time periods
    interface EventCache {
        locationId: number;
        events: Event[];
        fetchTime: Date;
        timeRange: TimeRange;
    }
    let eventCache = $state<EventCache | null>(null);

    // Check if cached data is still valid for the requested time range
    function isCacheValid(locId: number, requestedRange: TimeRange): boolean {
        if (!eventCache || eventCache.locationId !== locId) {
            return false;
        }

        // Check if cached time range covers the requested range
        const cacheStart = eventCache.timeRange.start.getTime();
        const cacheEnd = eventCache.timeRange.end.getTime();
        const requestStart = requestedRange.start.getTime();
        const requestEnd = requestedRange.end.getTime();

        // Cache is valid if it covers or equals the requested range
        return cacheStart <= requestStart && cacheEnd >= requestEnd;
    }

    // Filter cached events to the requested time range
    function filterCachedEvents(requestedRange: TimeRange): Event[] {
        if (!eventCache) return [];

        return eventCache.events.filter(event => {
            const eventTime = new Date(event.time).getTime();
            return eventTime >= requestedRange.start.getTime() &&
                   eventTime <= requestedRange.end.getTime();
        });
    }

    // Clear cache when location changes
    $effect(() => {
        if (locationId !== eventCache?.locationId) {
            eventCache = null;
            earliestEventTime = null; // Also clear earliest event time
        }
    });

    const ranges: { label: string; value: TimeRangeOption }[] = [
        { label: "Day", value: "day" },
        { label: "Week", value: "week" },
        { label: "Month", value: "month" },
        { label: "All", value: "all" },
        { label: "Custom", value: "custom" }
    ];

    // Color scheme
    const colors = {
        persons: {
            background: 'rgba(59, 130, 246, 0.7)',
            border: 'rgb(59, 130, 246)'
        },
        vehicles: {
            background: 'rgba(34, 197, 94, 0.7)',
            border: 'rgb(34, 197, 94)'
        },
        ppeBreaches: {
            background: 'rgba(251, 146, 60, 0.7)',
            border: 'rgb(251, 146, 60)'
        },
        zoneEntries: {
            background: 'rgba(239, 68, 68, 0.7)',
            border: 'rgb(239, 68, 68)'
        }
    };

    function toggleChartType() {
        const newType = currentChartType === 'bar' ? 'line' : 'bar';

        // Update global store (this will trigger the sync effect which updates currentChartType)
        chartPreferences.update(prefs => ({
            ...prefs,
            chartType: newType
        }));
    }

    async function loadChartData() {
        loading = true;
        try {
            // If "all" range is selected and we don't have earliest time yet, fetch it first
            if (selectedRange === 'all' && !earliestEventTime && USE_REAL_DATA && locationId) {
                // Fetch with fallback range to get all events
                const fallbackRange = calculateTimeRange('all', undefined);
                const allEventsResponse = await fetchEventsForLocation(locationId, fallbackRange);
                if (allEventsResponse.events.length > 0) {
                    earliestEventTime = findEarliestEventTime(allEventsResponse.events);
                    console.log(`📅 ChartModal: Found earliest event: ${earliestEventTime?.toISOString()}`);
                }
            }

            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined, earliestEventTime || undefined);

            // Create plain objects to avoid Svelte state descriptor issues
            const plainTimeRange = {
                start: new Date(timeRange.start),
                end: new Date(timeRange.end)
            };

            if (USE_REAL_DATA && locationId) {
                // ============================================
                // REAL DATA FROM API
                // ============================================
                let events: Event[];

                // Check if we can use cached data
                if (isCacheValid(locationId, plainTimeRange)) {
                    console.log('📦 ChartModal: Using cached events');
                    events = filterCachedEvents(plainTimeRange);
                } else {
                    // Fetch fresh events from API
                    const eventsResponse = await fetchEventsForLocation(locationId, plainTimeRange);
                    events = eventsResponse.events;

                    console.log(`✅ ChartModal: Fetched ${events.length} events from API`);

                    // Update cache with broader time range for day/week views
                    let cacheTimeRange = plainTimeRange;
                    if (selectedRange === 'day' || selectedRange === 'week') {
                        // Cache a month's worth of data when viewing day or week
                        const cacheStart = new Date(plainTimeRange.start);
                        cacheStart.setDate(1); // Start of month
                        cacheStart.setHours(0, 0, 0, 0);
                        const cacheEnd = new Date(cacheStart);
                        cacheEnd.setMonth(cacheEnd.getMonth() + 1);
                        cacheEnd.setDate(0); // Last day of month
                        cacheEnd.setHours(23, 59, 59, 999);

                        // If we need to fetch broader data
                        if (cacheStart.getTime() < plainTimeRange.start.getTime() ||
                            cacheEnd.getTime() > plainTimeRange.end.getTime()) {
                            const broadResponse = await fetchEventsForLocation(locationId, {
                                start: cacheStart,
                                end: cacheEnd
                            });
                            eventCache = {
                                locationId,
                                events: broadResponse.events,
                                fetchTime: new Date(),
                                timeRange: { start: cacheStart, end: cacheEnd }
                            };
                            console.log(`📦 ChartModal: Cached ${broadResponse.events.length} events for month range`);
                            // Filter to requested range
                            events = filterCachedEvents(plainTimeRange);
                        } else {
                            eventCache = {
                                locationId,
                                events,
                                fetchTime: new Date(),
                                timeRange: plainTimeRange
                            };
                        }
                    } else {
                        // Cache the exact range for month/all time views
                        eventCache = {
                            locationId,
                            events,
                            fetchTime: new Date(),
                            timeRange: plainTimeRange
                        };
                    }
                }

                // Transform events into chart data
                const chartData = createChartDataFromEvents(events, plainTimeRange);

                // Generate proper labels from timestamps
                const hoursDiff = Math.floor((plainTimeRange.end.getTime() - plainTimeRange.start.getTime()) / (1000 * 60 * 60));

                chartLabels = chartData.persons.map(point => {
                    const date = new Date(point.timestamp);

                    if (hoursDiff <= 24) {
                        // Day view - show hours
                        return `${date.getHours()}:00`;
                    } else if (hoursDiff <= 168) {
                        // Week view - show day names with dates
                        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                        return `${days[date.getDay()]} ${months[date.getMonth()]} ${date.getDate()}`;
                    } else if (hoursDiff <= 720) {
                        // Month view - show dates
                        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                        return `${months[date.getMonth()]} ${date.getDate()}`;
                    } else {
                        // All time - show week date ranges
                        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                        const weekEnd = new Date(date.getTime() + (6 * 24 * 60 * 60 * 1000)); // Add 6 days
                        const startMonth = months[date.getMonth()];
                        const endMonth = months[weekEnd.getMonth()];

                        if (date.getMonth() === weekEnd.getMonth()) {
                            // Same month: "Oct 1-7"
                            return `${startMonth} ${date.getDate()}-${weekEnd.getDate()}`;
                        } else {
                            // Different months: "Oct 28-Nov 3"
                            return `${startMonth} ${date.getDate()}-${endMonth} ${weekEnd.getDate()}`;
                        }
                    }
                });

                personsData = [...chartData.persons.map(point => point.value)];
                vehiclesData = [...chartData.vehicles.map(point => point.value)];
                ppeBreachesData = [...chartData.ppeBreaches.map(point => point.value)];
                zoneEntriesData = [...chartData.zoneEntries.map(point => point.value)];
            } else {
                // ============================================
                // MOCK DATA (Fallback or when USE_REAL_DATA = false)
                // ============================================
                const mockData = getMockChartModalData(plainTimeRange);

                chartLabels = [...mockData.labels];
                personsData = [...mockData.persons];
                vehiclesData = [...mockData.vehicles];
                ppeBreachesData = [...mockData.ppeBreaches];
                zoneEntriesData = [...mockData.zoneEntries];
            }

            updateChart();
        } catch (error) {
            console.error('Error loading chart data:', error);
            // Fallback to mock data on error
            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined);
            const plainTimeRange = {
                start: new Date(timeRange.start),
                end: new Date(timeRange.end)
            };
            const mockData = getMockChartModalData(plainTimeRange);
            chartLabels = [...mockData.labels];
            personsData = [...mockData.persons];
            vehiclesData = [...mockData.vehicles];
            ppeBreachesData = [...mockData.ppeBreaches];
            zoneEntriesData = [...mockData.zoneEntries];
            updateChart();
        } finally {
            loading = false;
        }
    }

    function initializeChart() {
        if (!canvasElement || chart) return;

        chart = new Chart(canvasElement, {
            type: currentChartType,
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top' as const,
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 14
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: initialTitle,
                        font: {
                            size: 20,
                            weight: 'bold'
                        },
                        padding: 25
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    function updateChart() {
        if (!chart) return;

        const datasets: any[] = [];

        if (showPersons) {
            datasets.push({
                label: 'Detected Persons',
                data: [...personsData],
                backgroundColor: colors.persons.background,
                borderColor: colors.persons.border,
                borderWidth: 2,
                tension: currentChartType === 'line' ? 0.4 : undefined,
                fill: currentChartType === 'line' ? false : undefined,
                pointRadius: currentChartType === 'line' ? 4 : undefined,
                pointHoverRadius: currentChartType === 'line' ? 6 : undefined
            });
        }

        if (showVehicles) {
            datasets.push({
                label: 'Detected Vehicles',
                data: [...vehiclesData],
                backgroundColor: colors.vehicles.background,
                borderColor: colors.vehicles.border,
                borderWidth: 2,
                tension: currentChartType === 'line' ? 0.4 : undefined,
                fill: currentChartType === 'line' ? false : undefined,
                pointRadius: currentChartType === 'line' ? 4 : undefined,
                pointHoverRadius: currentChartType === 'line' ? 6 : undefined
            });
        }

        if (showPPEBreaches) {
            datasets.push({
                label: 'PPE Breaches',
                data: [...ppeBreachesData],
                backgroundColor: colors.ppeBreaches.background,
                borderColor: colors.ppeBreaches.border,
                borderWidth: 2,
                tension: currentChartType === 'line' ? 0.4 : undefined,
                fill: currentChartType === 'line' ? false : undefined,
                pointRadius: currentChartType === 'line' ? 4 : undefined,
                pointHoverRadius: currentChartType === 'line' ? 6 : undefined
            });
        }

        if (showZoneEntries) {
            datasets.push({
                label: 'Zone Entries',
                data: [...zoneEntriesData],
                backgroundColor: colors.zoneEntries.background,
                borderColor: colors.zoneEntries.border,
                borderWidth: 2,
                tension: currentChartType === 'line' ? 0.4 : undefined,
                fill: currentChartType === 'line' ? false : undefined,
                pointRadius: currentChartType === 'line' ? 4 : undefined,
                pointHoverRadius: currentChartType === 'line' ? 6 : undefined
            });
        }

        chart.data.labels = [...chartLabels];
        chart.data.datasets = datasets;
        chart.update();
    }

    function handleTimeRangeChange(range: TimeRangeOption) {
        selectedRange = range;
        if (range === 'custom') {
            showCustomDatePicker = true;
        } else {
            customTimeRange = null;
            updateStore();
            loadChartData();
        }
    }

    function handleDateRangeApply(start: Date, end: Date) {
        customTimeRange = { start, end };
        selectedRange = 'custom';
        showCustomDatePicker = false;
        updateStore();
        loadChartData();
    }

    function closeCustomDatePicker() {
        showCustomDatePicker = false;
    }

    function updateStore() {
        chartPreferences.update(prefs => ({
            ...prefs,
            selectedRange,
            customTimeRange,
            showPersons,
            showVehicles,
            showPPEBreaches,
            showZoneEntries
        }));
    }

    function handleClose() {
        if (chart) {
            chart.destroy();
            chart = null;
        }
        prevChartType = null; // Reset tracking when closing
        onClose();
    }

    // Watch for toggle changes and update store
    $effect(() => {
        // Watch all checkboxes - accessing them makes this effect reactive to their changes
        const _ = [showPersons, showVehicles, showPPEBreaches, showZoneEntries];
        if (chart) {
            updateStore();
            updateChart();
        }
    });

    // Initialize chart when modal opens
    $effect(() => {
        if (open && canvasElement && !chart) {
            prevChartType = currentChartType; // Track initial type
            initializeChart();
            loadChartData();
        }
    });

    // Watch for chart type changes and recreate chart
    $effect(() => {
        // Access currentChartType to make this reactive
        const type = currentChartType;

        // Only recreate if:
        // 1. Chart exists
        // 2. Modal is open
        // 3. We've tracked a previous type
        // 4. Type actually changed
        if (chart && open && prevChartType !== null && prevChartType !== type) {
            console.log(`🔄 ChartModal: Chart type changed from ${prevChartType} to ${type}`);
            prevChartType = type;

            // Destroy old chart
            chart.destroy();
            chart = null;

            // Recreate with new type
            if (canvasElement) {
                initializeChart();
                updateChart();
            }
        } else if (!prevChartType && chart) {
            // Initialize tracking after first chart creation
            prevChartType = type;
            console.log(`📊 ChartModal: Initial chart type set to ${type}`);
        }
    });

    // Cleanup on destroy
    onDestroy(() => {
        if (chart) {
            chart.destroy();
        }
    });
</script>

{#if open}
    <!-- Backdrop -->
    <div
        class="fixed inset-0 backdrop-blur-sm bg-black/20 z-50 flex items-center justify-center p-4"
        onclick={handleClose}
        role="presentation"
    >
        <!-- Modal Content -->
        <div
            class="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
            onclick={(e) => e.stopPropagation()}
            onkeydown={(e) => e.key === 'Escape' && handleClose()}
            role="dialog"
            aria-modal="true"
            tabindex="-1"
        >
            <!-- Header -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                <h2 class="text-2xl font-bold text-gray-800">{initialTitle}</h2>
                <button
                    class="p-2 rounded-full hover:bg-gray-100 transition"
                    onclick={handleClose}
                    aria-label="Close modal"
                >
                    <X size={24} class="text-gray-600" />
                </button>
            </div>

            <!-- Content -->
            <div class="flex-1 overflow-y-auto p-6">
                <!-- Controls Section -->
                <div class="mb-6 space-y-4">
                    <!-- Time Range Selection & Chart Type Toggle -->
                    <div class="flex flex-wrap items-center justify-between gap-3">
                        <div class="flex flex-wrap items-center gap-3">
                            <span class="text-sm font-semibold text-gray-700">Time Period:</span>
                            {#each ranges as range}
                                <button
                                    class="px-4 py-2 rounded-lg text-sm font-medium transition {selectedRange === range.value
                                        ? 'bg-[#E76A23] text-white shadow-md'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                                    onclick={() => handleTimeRangeChange(range.value)}
                                >
                                    {range.label}
                                </button>
                            {/each}
                            {#if selectedRange === 'custom' && customTimeRange}
                                <span class="flex items-center text-sm text-gray-600 px-3 py-1 bg-orange-50 rounded-full border border-orange-200">
                                    {customTimeRange.start.toLocaleDateString('sv-SE')} - {customTimeRange.end.toLocaleDateString('sv-SE')}
                                </span>
                            {/if}
                        </div>

                        <!-- Chart Type Toggle Buttons -->
                        <div class="flex items-center gap-2">
                            <button
                                class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 {currentChartType === 'bar'
                                    ? 'bg-[#E76A23] text-white shadow-md'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                                onclick={() => currentChartType !== 'bar' && toggleChartType()}
                                title="Bar Chart"
                            >
                                <BarChart3 size={16} />
                            </button>
                            <button
                                class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1.5 {currentChartType === 'line'
                                    ? 'bg-[#E76A23] text-white shadow-md'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                                onclick={() => currentChartType !== 'line' && toggleChartType()}
                                title="Line Chart"
                            >
                                <LineChart size={16} />
                            </button>
                        </div>
                    </div>

                    <!-- Data Series Toggles -->
                    <div class="flex flex-wrap items-center gap-4">
                        <span class="text-sm font-semibold text-gray-700">Show Data:</span>

                        <label class="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                bind:checked={showPersons}
                                class="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <span class="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <span class="w-3 h-3 rounded" style="background-color: {colors.persons.border}"></span>
                                Persons
                            </span>
                        </label>

                        <label class="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                bind:checked={showVehicles}
                                class="w-4 h-4 text-green-600 rounded focus:ring-2 focus:ring-green-500"
                            />
                            <span class="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <span class="w-3 h-3 rounded" style="background-color: {colors.vehicles.border}"></span>
                                Vehicles
                            </span>
                        </label>

                        <label class="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                bind:checked={showPPEBreaches}
                                class="w-4 h-4 text-orange-600 rounded focus:ring-2 focus:ring-orange-500"
                            />
                            <span class="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <span class="w-3 h-3 rounded" style="background-color: {colors.ppeBreaches.border}"></span>
                                PPE Breaches
                            </span>
                        </label>

                        <label class="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                bind:checked={showZoneEntries}
                                class="w-4 h-4 text-red-600 rounded focus:ring-2 focus:ring-red-500"
                            />
                            <span class="flex items-center gap-2 text-sm font-medium text-gray-700">
                                <span class="w-3 h-3 rounded" style="background-color: {colors.zoneEntries.border}"></span>
                                Zone Entries
                            </span>
                        </label>
                    </div>
                </div>

                <!-- Chart Container -->
                <div class="bg-gray-50 rounded-xl p-6 relative" style="height: 500px;">
                    {#if loading}
                        <div class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 rounded-xl z-10">
                            <div class="text-center">
                                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E76A23] mx-auto mb-3"></div>
                                <p class="text-gray-600 font-medium">Loading data...</p>
                            </div>
                        </div>
                    {/if}
                    <canvas bind:this={canvasElement}></canvas>
                </div>

                <!-- Info Section -->
                <div class="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p class="text-sm text-blue-800">
                        <strong>Tip:</strong> Use the checkboxes above to show/hide different data series.
                        Change the time period to view data across different time ranges.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <DateRangePicker
        open={showCustomDatePicker}
        onClose={closeCustomDatePicker}
        onApply={handleDateRangeApply}
    />
{/if}

<style>
    /* Custom checkbox styling */
    input[type="checkbox"] {
        cursor: pointer;
    }

    input[type="checkbox"]:checked {
        accent-color: currentColor;
    }
</style>
