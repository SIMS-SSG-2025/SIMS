<script lang="ts">
    import BarChart from "$lib/components/BarChart.svelte";
    import PieChart from "$lib/components/PieChart.svelte";
    import Modal from "$lib/components/modal.svelte";
    import ConfigSetupModal from "$lib/components/ConfigSetupModal.svelte";
    import LogModal from "$lib/components/LogModal.svelte";
    import ChartModal from "$lib/components/ChartModal.svelte";
    import StatCard from "$lib/components/StatCard.svelte";
    import StatCardMulti from "$lib/components/StatCardMulti.svelte";
    import DateRangePicker from "$lib/components/DateRangePicker.svelte";
    import ZoneDrawer from "$lib/components/ZoneDrawer.svelte";
    import { onMount } from "svelte";
    import { fetchCurrentConfig, type Config } from "$lib/api/config";
    import {
        type DashboardStats,
        type TimeRangeOption,
        type TimeRange,
        type DetectionBarChartData,
        type PPEComplianceData,
        calculateTimeRange,
        fetchEventsForLocation,
        calculateStatsFromEvents,
        fetchDetectionBarChartData,
        fetchPPEComplianceData,
        getMockDetectionBarChartData,
        getMockChartModalData
    } from "$lib/api/stats";
    import { chartPreferences } from "$lib/stores/chartPreferences";

    import { Settings, Download, PersonStanding, Car, TriangleAlert, Ban } from "lucide-svelte";

    let now = $state(new Date());
    let interval: any;

    // Auto-subscribe to chart preferences store using Svelte 5 rune
    let preferences = $derived($chartPreferences);
    let selectedRange = $state<TimeRangeOption>('week');
    let customTimeRange = $state<TimeRange | null>(null);

    // Watch for store changes and sync local state
    $effect(() => {
        selectedRange = preferences.selectedRange;
        customTimeRange = preferences.customTimeRange;
    });

    // Track previous time range to detect changes
    let previousRange = $state<TimeRangeOption | null>(null);
    let previousCustomRange = $state<TimeRange | null>(null);

    // Only reload data when time range actually changes (not checkboxes)
    $effect(() => {
        const currentRange = preferences.selectedRange;
        const currentCustom = preferences.customTimeRange;

        // Skip initial run
        if (previousRange === null) {
            previousRange = currentRange;
            previousCustomRange = currentCustom;
            return;
        }

        // Only reload if time range changed (not checkbox changes)
        if (previousRange !== currentRange ||
            JSON.stringify(previousCustomRange) !== JSON.stringify(currentCustom)) {
            previousRange = currentRange;
            previousCustomRange = currentCustom;
            loadChartData();
        }
    });

    let activeTab = $state<'dashboard' | 'area'>('dashboard');

    let config = $state<Config | null>(null);
    let configLoading = $state(true);

    let stats = $state<DashboardStats>({
        detectedPersons: 0,
        detectedVehicles: 0,
        ppeBreaches: 0,
        helmetBreaches: 0,
        vestBreaches: 0,
        forbiddenZoneEntries: 0
    });
    let statsLoading = $state(false);

    // Chart data with all 4 series
    let chartLabels = $state<string[]>([]);
    let personsData = $state<number[]>([]);
    let vehiclesData = $state<number[]>([]);
    let ppeBreachesData = $state<number[]>([]);
    let zoneEntriesData = $state<number[]>([]);

    // Dynamically build datasets based on checkbox preferences
    let chartDatasets = $derived(() => {
        const datasets = [];
        if (preferences.showPersons) {
            datasets.push({
                label: 'Persons',
                data: personsData,
                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                borderColor: 'rgb(59, 130, 246)',
                borderWidth: 2
            });
        }
        if (preferences.showVehicles) {
            datasets.push({
                label: 'Vehicles',
                data: vehiclesData,
                backgroundColor: 'rgba(34, 197, 94, 0.7)',
                borderColor: 'rgb(34, 197, 94)',
                borderWidth: 2
            });
        }
        if (preferences.showPPEBreaches) {
            datasets.push({
                label: 'PPE Breaches',
                data: ppeBreachesData,
                backgroundColor: 'rgba(251, 146, 60, 0.7)',
                borderColor: 'rgb(251, 146, 60)',
                borderWidth: 2
            });
        }
        if (preferences.showZoneEntries) {
            datasets.push({
                label: 'Zone Entries',
                data: zoneEntriesData,
                backgroundColor: 'rgba(239, 68, 68, 0.7)',
                borderColor: 'rgb(239, 68, 68)',
                borderWidth: 2
            });
        }
        return datasets;
    });

    let ppeComplianceData = $state<PPEComplianceData>({
        compliant: 0,
        missingHardHat: 0,
        missingVest: 0,
        missingBoth: 0
    });

    // Normalize zones for ZoneDrawer (convert absolute coordinates to 0-1 range if needed)
    function normalizeZones(zones: any[], imageWidth: number, imageHeight: number) {
        if (!zones || zones.length === 0) return [];

        return zones.map(zone => ({
            ...zone,
            points: zone.points.map((p: any) => ({
                x: p.x > 1 ? p.x / imageWidth : p.x,
                y: p.y > 1 ? p.y / imageHeight : p.y
            }))
        }));
    }

    let lastFetchTime = $state<Date | null>(null);
    let pollingInterval: any;

    onMount(() => {
        interval = setInterval(() => {
            now = new Date();
        }, 1000);

        loadConfiguration();
        loadStatistics(true); // Initial load
        loadChartData(); // Initial chart load

        // Start polling every 5 seconds
        pollingInterval = setInterval(() => {
            loadStatistics(false); // Incremental load
        }, 5000);

        return () => {
            clearInterval(interval);
            clearInterval(pollingInterval);
        };
    });

    async function loadConfiguration() {
        configLoading = true;
        try {
            config = await fetchCurrentConfig();
            console.log("Loaded config:", $state.snapshot(config));

            // Reload statistics once config is available (we need location ID for real data)
            if (config && config.locationId) {
                await loadStatistics();
            }
        } catch (error) {
            console.error("Error loading configuration:", error);
            config = null;
        } finally {
            configLoading = false;
        }
    }

    async function loadStatistics(isInitialLoad = false) {
        statsLoading = true;
        try {
            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined);

            if (config && config.locationId) {
                try {
                    let response;

                    if (isInitialLoad || !lastFetchTime) {
                        // Initial load: fetch all data for the time range
                        response = await fetchEventsForLocation(config.locationId, timeRange);
                        lastFetchTime = new Date();

                        // Calculate stats for initial load
                        stats = calculateStatsFromEvents(response.events);
                        console.log("Loaded real stats from events:", $state.snapshot(stats));

                        // Load chart data separately
                        await loadChartData();

                        const ppeData = await fetchPPEComplianceData();
                        ppeComplianceData = ppeData;
                    } else {
                        // Incremental load: fetch only new events since last fetch
                        const incrementalRange = {
                            start: lastFetchTime,
                            end: new Date()
                        };
                        response = await fetchEventsForLocation(config.locationId, incrementalRange);

                        // Merge new events with existing stats
                        if (response.count > 0) {
                            const newStats = calculateStatsFromEvents(response.events);
                            stats = {
                                detectedPersons: stats.detectedPersons + newStats.detectedPersons,
                                detectedVehicles: stats.detectedVehicles + newStats.detectedVehicles,
                                ppeBreaches: stats.ppeBreaches + newStats.ppeBreaches,
                                helmetBreaches: stats.helmetBreaches + newStats.helmetBreaches,
                                vestBreaches: stats.vestBreaches + newStats.vestBreaches,
                                forbiddenZoneEntries: stats.forbiddenZoneEntries + newStats.forbiddenZoneEntries
                            };
                            console.log(`Added ${response.count} new events to stats`);
                        }

                        lastFetchTime = new Date();
                        // Don't update charts on incremental loads
                    }
                } catch (error) {
                    console.error("Error fetching events for stats:", error);
                    // Fallback to zeros on error
                    stats = {
                        detectedPersons: 0,
                        detectedVehicles: 0,
                        ppeBreaches: 0,
                        helmetBreaches: 0,
                        vestBreaches: 0,
                        forbiddenZoneEntries: 0
                    };
                }
            } else if (isInitialLoad) {
                // No config but initial load - load chart data
                loadChartData();
            }
        } catch (error) {
            console.error("Error loading statistics:", error);
        } finally {
            statsLoading = false;
        }
    }

    async function loadChartData() {
        try {
            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined);
            const mockData = getMockChartModalData(timeRange);
            const ppeData = await fetchPPEComplianceData();

            // Store all data series
            chartLabels = mockData.labels;
            personsData = mockData.persons;
            vehiclesData = mockData.vehicles;
            ppeBreachesData = mockData.ppeBreaches;
            zoneEntriesData = mockData.zoneEntries;

            // PPE compliance data (pie chart - just set to zeros if hidden)
            if (preferences.showPPEBreaches) {
                ppeComplianceData = ppeData;
            } else {
                ppeComplianceData = {
                    compliant: 0,
                    missingHardHat: 0,
                    missingVest: 0,
                    missingBoth: 0
                };
            }
        } catch (error) {
            console.error("Error loading chart data:", error);
        }
    }

    // Modal state
    let showSettingsModal = $state(false);
    let showConfigModal = $state(false);
    let showLogModal = $state(false);
    let showDateRangePicker = $state(false);
    let showChartModal = $state(false);
    let chartModalType = $state<'bar' | 'line'>('bar');
    let chartModalTitle = $state('Chart Details');

    function openSettingsModal() {
        showSettingsModal = true;
    }
    function closeSettingsModal() {
        showSettingsModal = false;
    }
    function openConfigModal() {
        showConfigModal = true;
    }
    function closeConfigModal() {
        showConfigModal = false;
        // Reload configuration after modal closes to reflect any changes
        loadConfiguration();
        // Reload stats with new config (reset for full load)
        lastFetchTime = null;
        loadStatistics(true);
    }
    function openLogModal() {
        showLogModal = true;
    }
    function closeLogModal() {
        showLogModal = false;
    }
    function openDateRangePicker() {
        showDateRangePicker = true;
    }
    function closeDateRangePicker() {
        showDateRangePicker = false;
    }
    function handleDateRangeApply(start: Date, end: Date) {
        customTimeRange = { start, end };
        selectedRange = 'custom';
        // Update global store
        chartPreferences.set({
            ...preferences,
            selectedRange: 'custom',
            customTimeRange: { start, end }
        });
        // Reload stats with new custom range
        lastFetchTime = null;
        loadStatistics(true);
    }

    function openChartModal(type: 'bar' | 'line', title: string) {
        chartModalType = type;
        chartModalTitle = title;
        showChartModal = true;
    }

    function closeChartModal() {
        showChartModal = false;
    }

    const ranges: { label: string; value: TimeRangeOption }[] = [
        { label: "Day", value: "day" },
        { label: "Week", value: "week" },
        { label: "Month", value: "month" },
        { label: "All", value: "all" },
        { label: "Custom", value: "custom" }
    ];

    function selectRange(val: TimeRangeOption) {
        const rangeChanged = selectedRange !== val;
        selectedRange = val;
        // If custom is selected, open the date picker
        if (val === 'custom') {
            openDateRangePicker();
        } else {
            customTimeRange = null;
            // Update global store
            chartPreferences.set({
                ...preferences,
                selectedRange: val,
                customTimeRange: null
            });
            // Reload stats if range actually changed
            if (rangeChanged && config?.locationId) {
                lastFetchTime = null;
                loadStatistics(true);
            }
        }
    }

</script>

<header class="w-full bg-gray-50 py-12">
    <div class="max-w-7xl mx-auto px-8 flex items-center justify-between">
        <!-- Left: Tab Navigation -->
        <div class="flex gap-2 bg-white p-1 rounded-lg shadow-sm">
            <button
                class="px-6 py-2 rounded-md font-semibold transition
                    {activeTab === 'dashboard'
                        ? 'bg-[#E76A23] text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'}"
                onclick={() => activeTab = 'dashboard'}
            >
                Dashboard
            </button>
            <button
                class="px-6 py-2 rounded-md font-semibold transition
                    {activeTab === 'area'
                        ? 'bg-[#E76A23] text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'}"
                onclick={() => activeTab = 'area'}
            >
                Area Management
            </button>
        </div>

        <!-- Right: Settings -->
        <div class="flex items-center gap-2">
            <button class="p-2 rounded-full hover:bg-gray-100 transition" aria-label="Export">
                <Download size={24} class="text-gray-600" />
            </button>
            <button class="p-2 rounded-full hover:bg-gray-100 transition" aria-label="Settings" onclick={openSettingsModal}>
                <Settings size={24} class="text-gray-600" />
            </button>
        </div>
    </div>
</header>

<Modal open={showSettingsModal} onClose={closeSettingsModal} modalClass="p-6 w-full max-w-md max-h-[90vh]">
    <div class="w-full">
        <h2 class="text-xl font-semibold text-gray-800 mb-6">Settings</h2>
        <div class="space-y-4">
            <button
                class="w-full px-4 py-3 bg-[#E76A23] text-white rounded-lg hover:bg-[#d15e1e] transition font-medium shadow-sm flex items-center justify-center gap-2"
                onclick={openLogModal}
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                    View Logs
                </button>
            </div>
        </div>
    </Modal>

<!-- MAIN CONTENT -->
<main class="bg-gray-50 min-h-screen">
    {#if activeTab === 'dashboard'}
        <!-- Time Range Selector (below header, only for dashboard) -->
        <div>
            <div class="max-w-7xl mx-auto px-8 flex gap-2">
                {#each ranges as r}
                    <button
                        class="px-4 py-2 rounded-lg font-semibold transition text-sm
                            {selectedRange === r.value
                                ? 'bg-[#E76A23] text-white'
                                : 'bg-white text-gray-700 hover:bg-orange-50 border border-gray-200'}"
                        onclick={() => selectRange(r.value)}
                    >
                        {r.label}
                    </button>
                {/each}
                {#if selectedRange === 'custom' && customTimeRange}
                    <span class="text-sm text-gray-600 ml-2 px-3 py-1 bg-orange-50 rounded-full border border-orange-200">
                        {customTimeRange.start.toLocaleDateString('sv-SE')} - {customTimeRange.end.toLocaleDateString('sv-SE')}
                    </span>
                {/if}
            </div>
        </div>

        <!-- Dashboard Content -->
        <div class="px-8 py-8 max-w-7xl mx-auto">
            <!-- Cards Row -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
            title="Detected Persons"
            value={stats.detectedPersons}
            iconColor="text-[#E76A23]"
            icon={`<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>`}
        />

        <StatCard
            title="Detected Vehicles"
            value={stats.detectedVehicles}
            iconColor="text-green-600"
            icon={`<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                <circle cx="9" cy="17" r="2" stroke="currentColor" stroke-width="2" fill="none"/>
                <circle cx="19" cy="17" r="2" stroke="currentColor" stroke-width="2" fill="none"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12h18l-2-6H5l-2 6zM3 12v5a1 1 0 001 1h1m14-6v5a1 1 0 01-1 1h-1" />
            </svg>`}
        />

        <StatCardMulti
            title="PPE Compliance Breaches"
            items={[
                {
                    label: 'Missing Hard Hat',
                    value: stats.helmetBreaches,
                    color: 'text-[#E76A23]',
                    icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 3C8 3 5 6 5 9v3h14V9c0-3-3-6-7-6z"/>
                        <path d="M5 12v2c0 1 1 2 2 2h10c1 0 2-1 2-2v-2H5z"/>
                        <circle cx="12" cy="8" r="1" fill="currentColor"/>
                    </svg>`
                },
                {
                    label: 'Missing Safety Vest',
                    value: stats.vestBreaches,
                    color: 'text-[#E76A23]',
                    icon: `<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 3l-3 3v15h14V6l-3-3"/>
                        <path d="M8 3c0 2 1 3 2 4 1 1 2 1 2 1s1 0 2-1c1-1 2-2 2-4"/>
                        <line x1="7" y1="10" x2="9" y2="10" stroke-width="3"/>
                        <line x1="15" y1="10" x2="17" y2="10" stroke-width="3"/>
                        <line x1="7" y1="14" x2="9" y2="14" stroke-width="3"/>
                        <line x1="15" y1="14" x2="17" y2="14" stroke-width="3"/>
                    </svg>`
                }
            ]}
            iconColor="text-orange-600"
            icon={`<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>`}
        />

        <StatCard
            title="Forbidden Zone Entries"
            value={stats.forbiddenZoneEntries}
            iconColor="text-red-600"
            icon={`<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>`}
        />
    </div>

    <!-- Charts Row (2 charts only) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Detection Bar Chart - Persons & Vehicles -->
        <div
            class="bg-white rounded-2xl shadow p-6 min-h-[400px] flex flex-col cursor-pointer hover:shadow-xl transition-shadow duration-200 group"
            onclick={() => openChartModal('bar', 'Detections Over Time')}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && openChartModal('bar', 'Detections Over Time')}
        >
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-700">Detections Over Time</h3>
                <svg
                    class="w-5 h-5 text-gray-400 group-hover:text-[#E76A23] transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m0 0v6m0-6h6m-6 0H4" />
                </svg>
            </div>
            <div class="flex-1">
                <BarChart
                    labels={chartLabels}
                    datasets={chartDatasets()}
                />
            </div>
            <p class="text-xs text-gray-500 text-center mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                Click to expand and customize
            </p>
        </div>

        <!-- PPE Compliance Pie Chart -->
        <div class="bg-white rounded-2xl shadow p-6 min-h-[400px] flex flex-col">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-700">PPE Compliance Breakdown</h3>
            </div>
            <div class="flex-1">
                <PieChart
                    labels={['Compliant', 'Missing Hard Hat', 'Missing Vest', 'Missing Both']}
                    data={[
                        ppeComplianceData.compliant,
                        ppeComplianceData.missingHardHat,
                        ppeComplianceData.missingVest,
                        ppeComplianceData.missingBoth
                    ]}
                    backgroundColor={[
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(251, 146, 60, 0.8)',
                        'rgba(234, 179, 8, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ]}
                    isDoughnut={true}
                />
            </div>
        </div>
    </div>
        </div>
    {:else if activeTab === 'area'}
        <!-- Area Management Content -->
        <div class="px-8 max-w-7xl mx-auto">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-gray-800">Area Management</h2>
                <button
                    class="px-4 py-2 rounded-lg bg-[#E76A23] text-white hover:bg-[#d15e1e] transition font-medium shadow-sm flex items-center gap-2"
                    onclick={openConfigModal}
                    aria-label="Setup Configuration"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
                    </svg>
                    Setup Configuration
                </button>
            </div>

            <!-- Snapshot with Zones -->
            <div class="bg-white rounded-2xl shadow p-6">
                <h3 class="text-lg font-semibold text-gray-700 mb-4">Camera View with Zones</h3>
                <div class="p-6 flex items-center justify-center bg-gray-100 rounded-lg overflow-hidden" style="height: 600px;">
                    {#if config && config.snapshotPath}
                        <div class="w-full max-w-2xl max-h-full">
                            <ZoneDrawer
                                zones={normalizeZones(config.zones || [], 1920, 1080)}
                                imageSrc={config.snapshotPath}
                                width={1200}
                                height={675}
                                readOnly={true}
                                onFinishZone={() => {}}
                            />
                        </div>
                    {:else}
                        <div class="text-center">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <p class="text-gray-500 text-lg font-medium mb-2">No snapshot available</p>
                            <p class="text-gray-400 text-sm">Configure camera settings to capture a snapshot</p>
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    {/if}

    <ConfigSetupModal
        open={showConfigModal}
        onClose={closeConfigModal}
    />

    <LogModal
        open={showLogModal}
        onClose={closeLogModal}
    />

    <DateRangePicker
        open={showDateRangePicker}
        onClose={closeDateRangePicker}
        onApply={handleDateRangeApply}
    />

    <ChartModal
        bind:open={showChartModal}
        onClose={closeChartModal}
        chartType={chartModalType}
        initialTitle={chartModalTitle}
        locationId={config?.locationId}
    />
</main>

<style>
    :global(body) {
        background: #f9fafb;
    }
</style>
