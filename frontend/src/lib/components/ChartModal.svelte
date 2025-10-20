<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { Chart, Title, Tooltip, Legend, BarElement, LineElement, PointElement, CategoryScale, LinearScale, BarController, LineController } from 'chart.js';
    import { X } from 'lucide-svelte';
    import type { TimeRangeOption, TimeRange } from '$lib/api/stats';
    import {
        calculateTimeRange,
        getMockChartModalData,
        fetchEventsForLocation,
        createChartDataFromEvents,
        calculatePPEComplianceFromEvents
    } from '$lib/api/stats';
    import { chartPreferences } from '$lib/stores/chartPreferences';
    import DateRangePicker from './DateRangePicker.svelte';

    // ============================================
    // DATA SOURCE CONFIGURATION
    // ============================================
    // Set this to false to use mock data for charts
    const USE_REAL_DATA = true;

    Chart.register(
        Title, Tooltip, Legend,
        BarElement, LineElement, PointElement,
        CategoryScale, LinearScale,
        BarController, LineController
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

    // Sync local state when store changes
    $effect(() => {
        showPersons = preferences.showPersons;
        showVehicles = preferences.showVehicles;
        showPPEBreaches = preferences.showPPEBreaches;
        showZoneEntries = preferences.showZoneEntries;
        selectedRange = preferences.selectedRange;
        customTimeRange = preferences.customTimeRange;
    });

    let showCustomDatePicker = $state(false);

    // Chart data
    let chartLabels = $state<string[]>([]);
    let personsData = $state<number[]>([]);
    let vehiclesData = $state<number[]>([]);
    let ppeBreachesData = $state<number[]>([]);
    let zoneEntriesData = $state<number[]>([]);

    let canvasElement: HTMLCanvasElement | undefined;
    let chart: Chart | null = null;
    let loading = $state(false);

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

    async function loadChartData() {
        loading = true;
        try {
            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined);

            // Create plain objects to avoid Svelte state descriptor issues
            const plainTimeRange = {
                start: new Date(timeRange.start),
                end: new Date(timeRange.end)
            };

            if (USE_REAL_DATA && locationId) {
                // ============================================
                // REAL DATA FROM API
                // ============================================
                const eventsResponse = await fetchEventsForLocation(locationId, plainTimeRange);
                const events = eventsResponse.events;

                // Transform events into chart data
                const chartData = createChartDataFromEvents(events, plainTimeRange);

                // Convert ChartDataPoint[] to labels and data arrays
                const hoursDiff = Math.floor((plainTimeRange.end.getTime() - plainTimeRange.start.getTime()) / (1000 * 60 * 60));

                chartLabels = chartData.persons.map(point => {
                    const date = new Date(point.timestamp);

                    if (hoursDiff <= 24) {
                        // Day view - show hours
                        return `${date.getHours()}:00`;
                    } else if (hoursDiff <= 168) {
                        // Week view - show day names with date
                        return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                    } else if (hoursDiff <= 720) {
                        // Month view - show dates
                        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    } else {
                        // All time - show weeks
                        const weekNumber = Math.floor((date.getTime() - plainTimeRange.start.getTime()) / (1000 * 60 * 60 * 24 * 7)) + 1;
                        return `Week ${weekNumber}`;
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
            type: chartType,
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
                tension: chartType === 'line' ? 0.4 : undefined,
                fill: chartType === 'line' ? false : undefined,
                pointRadius: chartType === 'line' ? 4 : undefined,
                pointHoverRadius: chartType === 'line' ? 6 : undefined
            });
        }

        if (showVehicles) {
            datasets.push({
                label: 'Detected Vehicles',
                data: [...vehiclesData],
                backgroundColor: colors.vehicles.background,
                borderColor: colors.vehicles.border,
                borderWidth: 2,
                tension: chartType === 'line' ? 0.4 : undefined,
                fill: chartType === 'line' ? false : undefined,
                pointRadius: chartType === 'line' ? 4 : undefined,
                pointHoverRadius: chartType === 'line' ? 6 : undefined
            });
        }

        if (showPPEBreaches) {
            datasets.push({
                label: 'PPE Breaches',
                data: [...ppeBreachesData],
                backgroundColor: colors.ppeBreaches.background,
                borderColor: colors.ppeBreaches.border,
                borderWidth: 2,
                tension: chartType === 'line' ? 0.4 : undefined,
                fill: chartType === 'line' ? false : undefined,
                pointRadius: chartType === 'line' ? 4 : undefined,
                pointHoverRadius: chartType === 'line' ? 6 : undefined
            });
        }

        if (showZoneEntries) {
            datasets.push({
                label: 'Zone Entries',
                data: [...zoneEntriesData],
                backgroundColor: colors.zoneEntries.background,
                borderColor: colors.zoneEntries.border,
                borderWidth: 2,
                tension: chartType === 'line' ? 0.4 : undefined,
                fill: chartType === 'line' ? false : undefined,
                pointRadius: chartType === 'line' ? 4 : undefined,
                pointHoverRadius: chartType === 'line' ? 6 : undefined
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
        chartPreferences.set({
            selectedRange,
            customTimeRange,
            showPersons,
            showVehicles,
            showPPEBreaches,
            showZoneEntries
        });
    }

    function handleClose() {
        if (chart) {
            chart.destroy();
            chart = null;
        }
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
            initializeChart();
            loadChartData();
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
                    <!-- Time Range Selection -->
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
