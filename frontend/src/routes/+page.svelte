
<script lang="ts">
    import LineChart from "$lib/components/LineChart.svelte";
    import Modal from "$lib/components/modal.svelte";
    import ConfigSetupModal from "$lib/components/ConfigSetupModal.svelte";
    import LogModal from "$lib/components/LogModal.svelte";
    import { onMount } from "svelte";
    import { fetchCurrentConfig, type Config } from "$lib/api/config";

    let now = new Date();
    let interval: any;
    let selectedRange: "day" | "week" | "month" | "all" = "day";

    let config: Config | null = null;
    let configLoading = true;


    onMount(() => {
        interval = setInterval(() => {
            now = new Date();
        }, 1000);

        loadConfiguration();

        return () => {
            clearInterval(interval);
        };
    });

    async function loadConfiguration() {
        configLoading = true;
        try {
            config = await fetchCurrentConfig();
            console.log("Loaded config:", config);
        } catch (error) {
            console.error("Error loading configuration:", error);
            config = null;
        } finally {
            configLoading = false;
        }
    }

        // Modal state
    let showZoneModal = false;
    let showSettingsModal = false;
    let showConfigModal = false;
    let showLogModal = false;

    function openZoneModal() {
        showZoneModal = true;
    }
    function closeZoneModal() {
        showZoneModal = false;
    }
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

    const ranges: { label: string; value: "day" | "week" | "month" | "all" }[] = [
        { label: "Day", value: "day" },
        { label: "Week", value: "week" },
        { label: "Month", value: "month" },
        { label: "All", value: "all" }
    ];

    function selectRange(val: typeof selectedRange) {
        selectedRange = val;
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

<header class="w-full bg-white shadow flex items-center justify-between px-8 py-4">
    <!-- Left: Date & Time + Location -->
    <div class="flex items-center min-w-[180px] gap-4">
        <span class="text-gray-700 font-mono text-lg select-none">
            {now.toLocaleDateString('sv-SE')} {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
        </span>
        {#if config}
            <span class="text-sm text-gray-600 border-l pl-4">
                {config.locationName}
            </span>
        {:else if configLoading}
            <span class="text-sm text-gray-400 border-l pl-4">
                Loading...
            </span>
        {/if}
    </div>

    <!-- Center: Range Buttons -->
    <div class="flex gap-2">
        {#each ranges as r}
            <button
                class="px-4 py-2 rounded-full font-semibold transition
                    {selectedRange === r.value
                        ? 'bg-blue-600 text-white shadow'
                        : 'bg-gray-100 text-gray-700 hover:bg-blue-50'}"
                on:click={() => selectRange(r.value)}
            >
                {r.label}
            </button>
        {/each}
    </div>
<!-- Right: Export & Settings -->
    <div class="flex items-center gap-2 min-w-[120px] justify-end">
        <button
            class="px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition font-medium text-sm shadow-sm"
            on:click={openConfigModal}
            aria-label="Setup Configuration"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1.5 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
            </svg>
            Setup
        </button>
        <button class="p-2 rounded-full hover:bg-gray-100 transition" aria-label="Export">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
        </button>
        <button class="p-2 rounded-full hover:bg-gray-100 transition" aria-label="Settings" on:click={openSettingsModal}>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6l4 2" />
            </svg>
        </button>
    <Modal open={showSettingsModal} onClose={closeSettingsModal} modalClass="p-6 w-full max-w-md max-h-[90vh]">
        <div class="w-full">
            <h2 class="text-xl font-semibold text-gray-800 mb-6">Settings</h2>
            <div class="space-y-4">
                <button
                    class="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium shadow-sm flex items-center justify-center gap-2"
                    on:click={openLogModal}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    View Logs
                </button>
            </div>
        </div>
    </Modal>
    </div>
</header>

<!-- MAIN DASHBOARD CONTENT -->
<main class="bg-gray-50 min-h-screen px-8 py-8">
    <!-- Cards Row -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {#each Array(4) as _, i}
            <div class="bg-white rounded-2xl shadow p-6 flex flex-col items-center justify-center min-h-[120px]">
                <span class="text-2xl font-bold text-gray-800">Card {i + 1}</span>
                <span class="text-gray-400 mt-2">Counter or stat</span>
            </div>
        {/each}
    </div>

    <!-- Graphs & Snapshot Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="bg-white rounded-2xl shadow p-6 min-h-[320px] flex flex-col">
            <span class="text-lg font-semibold text-gray-700 mb-2">Line Chart</span>
            <div class="flex-1 flex items-center justify-center text-gray-300"><LineChart /></div>
        </div>
        <div class="bg-white rounded-2xl shadow p-6 min-h-[320px] flex flex-col">
            <span class="text-lg font-semibold text-gray-700 mb-2">Line Chart</span>
            <div class="flex-1 flex items-center justify-center text-gray-300"><LineChart /></div>
        </div>
    </div>

    <!-- Log & Info Row (3 cards) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div class="bg-white rounded-2xl shadow p-6 flex flex-col items-center justify-center min-h-[120px]">
            <span class="text-2xl font-bold text-gray-800">Card A</span>
            <span class="text-gray-400 mt-2">Info or stat</span>
        </div>
        <div class="bg-white rounded-2xl shadow p-6 flex flex-col items-center justify-center min-h-[120px]">
            <span class="text-2xl font-bold text-gray-800">Card B</span>
            <span class="text-gray-400 mt-2">Info or stat</span>
        </div>
        <div class="bg-white rounded-2xl shadow p-6 flex flex-col items-center justify-center min-h-[120px]">
            <span class="text-2xl font-bold text-gray-800">Card C</span>
            <span class="text-gray-400 mt-2">Info or stat</span>
        </div>
    </div>

    <ConfigSetupModal
        open={showConfigModal}
        onClose={closeConfigModal}
    />

    <LogModal
        open={showLogModal}
        onClose={closeLogModal}
    />
</main>

<style>
    :global(body) {
        background: #f9fafb;
    }
</style>
