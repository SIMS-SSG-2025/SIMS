
<script lang="ts">
    import LineChart from "$lib/components/LineChart.svelte";
    import BarChart from "$lib/components/BarChart.svelte";
    import PieChart from "$lib/components/PieChart.svelte";
    import Modal from "$lib/components/modal.svelte";
    import ConfigSetupModal from "$lib/components/ConfigSetupModal.svelte";
    import LogModal from "$lib/components/LogModal.svelte";
    import StatCard from "$lib/components/StatCard.svelte";
    import DateRangePicker from "$lib/components/DateRangePicker.svelte";
    import { onMount } from "svelte";
    import { fetchCurrentConfig, type Config } from "$lib/api/config";
    import {
        type DashboardStats,
        type TimeRangeOption,
        type TimeRange,
        type DetectionBarChartData,
        type PPEComplianceData,
        calculateTimeRange,
        fetchStats,
        fetchDetectionBarChartData,
        fetchPPEComplianceData
    } from "$lib/api/stats";

    import { Settings, Download, PersonStanding, Car, TriangleAlert, Ban } from "lucide-svelte";

    let now = $state(new Date());
    let interval: any;
    let selectedRange = $state<TimeRangeOption>("day");
    let customTimeRange = $state<TimeRange | null>(null);
    let activeTab = $state<'dashboard' | 'area'>('dashboard');

    let config = $state<Config | null>(null);
    let configLoading = $state(true);

    let stats = $state<DashboardStats>({
        detectedPersons: 0,
        detectedVehicles: 0,
        ppeBreaches: 0,
        forbiddenZoneEntries: 0
    });
    let statsLoading = $state(false);

    let detectionChartData = $state<DetectionBarChartData>({
        labels: [],
        persons: [],
        vehicles: []
    });

    let ppeComplianceData = $state<PPEComplianceData>({
        compliant: 0,
        missingHardHat: 0,
        missingVest: 0,
        missingBoth: 0
    });


    onMount(() => {
        interval = setInterval(() => {
            now = new Date();
        }, 1000);

        loadConfiguration();
        loadStatistics();

        return () => {
            clearInterval(interval);
        };
    });

    async function loadConfiguration() {
        configLoading = true;
        try {
            config = await fetchCurrentConfig();
            console.log("Loaded config:", $state.snapshot(config));
        } catch (error) {
            console.error("Error loading configuration:", error);
            config = null;
        } finally {
            configLoading = false;
        }
    }

    async function loadStatistics() {
        statsLoading = true;
        try {
            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined);

            // Load all data in parallel
            const [statsData, chartData, ppeData] = await Promise.all([
                fetchStats(timeRange),
                fetchDetectionBarChartData(timeRange),
                fetchPPEComplianceData()
            ]);

            stats = statsData;
            detectionChartData = chartData;
            ppeComplianceData = ppeData;

            console.log("Loaded stats:", $state.snapshot(stats));
            console.log("Loaded chart data:", $state.snapshot(detectionChartData));
            console.log("Loaded PPE data:", $state.snapshot(ppeComplianceData));
        } catch (error) {
            console.error("Error loading statistics:", error);
        } finally {
            statsLoading = false;
        }
    }

    // Reload stats when time range changes
    $effect(() => {
        if (selectedRange) {
            loadStatistics();
        }
    });

        // Modal state
    let showSettingsModal = $state(false);
    let showConfigModal = $state(false);
    let showLogModal = $state(false);
    let showDateRangePicker = $state(false);

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
    }

    const ranges: { label: string; value: TimeRangeOption }[] = [
        { label: "Day", value: "day" },
        { label: "Week", value: "week" },
        { label: "Month", value: "month" },
        { label: "All", value: "all" },
        { label: "Custom", value: "custom" }
    ];

    function selectRange(val: TimeRangeOption) {
        selectedRange = val;
        // If custom is selected, open the date picker
        if (val === 'custom') {
            openDateRangePicker();
        } else {
            customTimeRange = null;
        }
    }

    let snapshotURL: string | null = null;
    let loading = false;
    let error: string | null = null;

    type Event = {
        message: string;
    };

    let events: Event[] = [];

    async function loadEvents() {
        loading = true;
        error = null;
        try {
            const response = await fetch("http://10.10.67.45:8000/events");
            if (!response.ok) {
                throw new Error(`Error fetching events: ${response.statusText}`);
            }
            events = await response.json();
            console.log(events);
        } catch (err: any) {
            error = err.message;
        } finally {
            loading = false;
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

        <StatCard
            title="PPE Compliance Breaches"
            value={stats.ppeBreaches}
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
        <div class="bg-white rounded-2xl shadow p-6 min-h-[400px] flex flex-col">
            <h3 class="text-lg font-semibold text-gray-700 mb-4">Detections Over Time</h3>
            <div class="flex-1">
                <BarChart
                    labels={detectionChartData.labels}
                    datasets={[
                        {
                            label: 'Persons',
                            data: detectionChartData.persons,
                            backgroundColor: 'rgba(231, 106, 35, 0.7)',
                            borderColor: 'rgb(231, 106, 35)',
                            borderWidth: 2
                        },
                        {
                            label: 'Vehicles',
                            data: detectionChartData.vehicles,
                            backgroundColor: 'rgba(34, 197, 94, 0.7)',
                            borderColor: 'rgb(34, 197, 94)',
                            borderWidth: 2
                        }
                    ]}
                />
            </div>
        </div>

        <!-- PPE Compliance Pie Chart -->
        <div class="bg-white rounded-2xl shadow p-6 min-h-[400px] flex flex-col">
            <h3 class="text-lg font-semibold text-gray-700 mb-4">PPE Compliance Breakdown</h3>
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
        <div class="px-8 py-8 max-w-7xl mx-auto">
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
                <div class="relative bg-gray-100 rounded-lg overflow-hidden" style="min-height: 600px;">
                    {#if config && config.snapshotPath}
                        <img
                            src={config.snapshotPath}
                            alt="Camera snapshot"
                            class="w-full h-auto"
                        />
                        <!-- Zone overlays -->
                        {#if config.zones && config.zones.length > 0}
                            <svg class="absolute top-0 left-0 w-full h-full pointer-events-none">
                                {#each config.zones as zone, i}
                                    <polygon
                                        points={zone.points.map((p: any) => `${p.x},${p.y}`).join(' ')}
                                        fill={i % 2 === 0 ? 'rgba(231, 106, 35, 0.3)' : 'rgba(239, 68, 68, 0.3)'}
                                        stroke={i % 2 === 0 ? 'rgb(231, 106, 35)' : 'rgb(239, 68, 68)'}
                                        stroke-width="2"
                                    />
                                    <text
                                        x={zone.points[0].x}
                                        y={zone.points[0].y - 5}
                                        fill={i % 2 === 0 ? 'rgb(231, 106, 35)' : 'rgb(239, 68, 68)'}
                                        font-size="14"
                                        font-weight="bold"
                                    >
                                        {zone.name}
                                    </text>
                                {/each}
                            </svg>
                        {/if}
                    {:else}
                        <div class="flex items-center justify-center h-full min-h-[600px]">
                            <div class="text-center">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                                </svg>
                                <p class="text-gray-500 text-lg">No snapshot available</p>
                                <p class="text-gray-400 text-sm mt-2">Configure camera settings to capture a snapshot</p>
                            </div>
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
</main>

<style>
    :global(body) {
        background: #f9fafb;
    }
</style>
