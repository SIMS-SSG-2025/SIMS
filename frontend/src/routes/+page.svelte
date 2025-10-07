
<script lang="ts">
    import TablePlaceholder from "$lib/components/TablePlaceholder.svelte";
    import LineChart from "$lib/components/LineChart.svelte";
    import ZoneDrawer from "$lib/components/ZoneDrawer.svelte";
    import Modal from "$lib/components/modal.svelte";
    import { onMount } from "svelte";

    let now = new Date();
    let interval: any;
    let selectedRange: "day" | "week" | "month" | "all" = "day";

    type Zone = {
        points: { x: number; y: number }[];
        name: string;
    }

    let zones: Zone[] = [];
    let showZones = true;

    onMount(() => {
        interval = setInterval(() => {
            now = new Date();
        }, 1000);

        return () => {
            clearInterval(interval);
        };
    });

        // Modal state
    let showZoneModal = false;
    let showSettingsModal = false;
    let showSetupModal = false;

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
    function openSetupModal() { showSetupModal = true; }
    function closeSetupModal() { showSetupModal = false; }

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

    function removeZone(index: number) {
        zones = zones.slice(0, index).concat(zones.slice(index + 1));
    }

    async function fetchSnapshot() {
        loading = true;
        error = null;
        try {
            // Try fetching from the live server first (if available)
            const response = await fetch("http://10.10.67.44:8000/snapshot");
            if (response.ok) {
                const blob = await response.blob();
                snapshotURL = URL.createObjectURL(blob);
            } else {
                // fallback to static snapshot in the app
                snapshotURL = '/snapshot.jpg';
            }
        } catch (err: any) {
            // If server not available, use the static snapshot packaged with the frontend
            snapshotURL = '/snapshot.jpg';
            error = null; // don't show an error for this expected fallback
        } finally {
            loading = false;
        }
    }

    // Setups state and handlers
    type Setup = { id?: number; location: string; zones: Zone[]; created_at?: string };
    let setups: Setup[] = [];
    let newSetup: Setup = { location: "", zones: [] };

    async function loadSetups() {
        try {
            const res = await fetch("http://127.0.0.1:8000/setups");
            if (res.ok) {
                const data = await res.json();
                setups = data.setups || [];
            } else {
                setups = [];
            }
        } catch (e) {
            // backend may not be running — silently fallback to empty list
            setups = [];
        }
    }
    function addNewSetupZone(points: { x: number; y: number }[], name: string) {
        newSetup.zones = [...newSetup.zones, { points, name }];
    }
    function removeNewSetupZone(index: number) {
        newSetup.zones = newSetup.zones.slice(0, index).concat(newSetup.zones.slice(index + 1));
    }
    async function saveSetup() {
        if (!newSetup.location) { alert("Please enter a location name"); return; }
        try {
            const res = await fetch("http://127.0.0.1:8000/setups", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ location: newSetup.location, zones: newSetup.zones })
            });
            const data = await res.json();
            if (data.status === "success") {
                await loadSetups();
                newSetup = { location: "", zones: [] };
            } else {
                alert(data.message || "Failed to save setup");
            }
        } catch (e) { console.error(e); }
    }
    async function startSetup() {
        try {
            const res = await fetch("http://127.0.0.1:8000/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ location: newSetup.location, zones: newSetup.zones })
            });
            const data = await res.json();
            if (data.status === "started") {
                closeSetupModal();
            }
        } catch (e) { console.error(e); }
    }
    function openSetupFlow() {
        openSetupModal();
        loadSetups();
    }

    // Setup modal tab state
    let setupTab: 1 | 2 | 3 = 1;
    function gotoTab(n: 1 | 2 | 3) {
        setupTab = n;
        // If user navigates to the Snapshot tab and there's no snapshot yet,
        // use the static snapshot so the ZoneDrawer always has an image to show.
        if (n === 2 && !snapshotURL) {
            snapshotURL = '/snapshot.jpg';
        }
    }
    $: progress = setupTab === 1 ? 33 : setupTab === 2 ? 66 : 100;

    type Event = {
        message: string;
    };

    let events: Event[] = [];

    let logs: string[] = [];

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

    async function sendZone(points: { x: number; y: number }[], name: string) {

        zones = [...zones, { points, name }];
        const response = await fetch("http://127.0.0.1:8000/zones", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ points, name })
        });
        const data = await response.json();
        console.log(data);
    }

    async function fetchLogs() {
        try {
            // IP jetson: 10.10.67.44
            const response = await fetch("http://10.10.67.44:8000/logs");
            if (!response.ok) {
                throw new Error(`Error fetching logs: ${response.statusText}`);
            }
            const data = await response.json();
            console.log(data);
            logs = data.logs || [];
        } catch (err: any) {
            error = err.message;
        } finally {
            loading = false;
        }
    }
    let logInterval: any;
    onMount(() => {
        logInterval = setInterval(fetchLogs, 5000);
        fetchLogs(); // Initial fetch
        return () => {
            clearInterval(logInterval);
        };
    });

</script>

<header class="w-full bg-white shadow flex items-center justify-between px-8 py-4">
    <!-- Left: Date & Time -->
    <div class="flex items-center min-w-[180px]">
        <span class="text-gray-700 font-mono text-lg select-none">
            {now.toLocaleDateString('sv-SE')} {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
        </span>
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
        <button class="px-3 py-1.5 rounded-full bg-green-600 text-white font-semibold shadow hover:bg-green-700 transition" on:click={openSetupFlow}>
            Setup & Start
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
    <Modal open={showSettingsModal} onClose={closeSettingsModal} modalClass="p-0 w-full max-w-md max-h-[90vh]">
        <span class="text-lg font-semibold text-gray-700 mb-2 mt-6">Settings</span>
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
        <div class="bg-white rounded-2xl shadow p-6 min-h-[320px] flex flex-col items-center justify-center">
            <img src="/snapshot.jpg" alt="Snapshot" class="rounded-xl shadow max-w-full max-h-64 object-contain border border-gray-200 mb-4" />
            <button
                class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-full font-semibold shadow hover:bg-blue-700 transition"
                on:click={openZoneModal}
            >
                Draw Zones
            </button>
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
        <div class="bg-white rounded-2xl shadow p-6 flex flex-col min-h-[120px]">
            <div class="flex-1 w-full max-h-32 overflow-y-auto text-sm text-gray-700 bg-gray-50 rounded p-2 border border-gray-200">
                {#if logs.length > 0}
                    <ul class="space-y-1">
                        {#each logs as log}
                            <li class="whitespace-pre-line">{log}</li>
                        {/each}
                    </ul>
                {:else}
                    <div>No log messages yet.</div>
                {/if}
            </div>
        </div>
    </div>

    <Modal open={showZoneModal} onClose={closeZoneModal} modalClass="p-0 w-full max-w-6xl max-h-[95vh]">
        <span class="text-lg font-semibold text-gray-700 mb-2 mt-6">Draw Zones on Snapshot</span>
        <div class="flex flex-col items-center p-6 w-full">
            <div class="w-full" style="max-width:1200px;">
                <div class="flex items-center mb-4 gap-4">
                    <button
                        class="px-4 py-2 rounded-full font-semibold transition bg-blue-600 text-white shadow hover:bg-blue-700"
                        on:click={() => showZones = !showZones}
                    >
                        {showZones ? "Hide Zones" : "Show Zones"}
                    </button>
                    <span class="text-gray-600">Zones: {zones.length}</span>
                    <div class="flex gap-2 flex-wrap">
                        {#each zones as zone, i}
                            <span class="inline-flex items-center bg-blue-100 text-blue-800 rounded px-2 py-1 text-xs font-semibold mr-2">
                                {zone.name || `Zone ${i + 1}`}
                                <button
                                    class="ml-1 text-red-500 hover:text-red-700 focus:outline-none"
                                    title="Remove zone"
                                    on:click={() => removeZone(i)}
                                >&#10005;</button>
                            </span>
                        {/each}
                    </div>
                </div>
                <ZoneDrawer
                    onFinishZone={sendZone}
                    width={1200}
                    height={675}
                    {zones}
                    {showZones}
                />
            </div>
        </div>
    </Modal>

    <!-- Setup & Start Modal -->
    <Modal open={showSetupModal} onClose={closeSetupModal} modalClass="p-0 w-full max-w-6xl max-h-[95vh]">
        <div class="p-0 w-full">
            <!-- Tabs as the modal header -->
            <div class="bg-gray-50 border-b border-gray-200 px-6 py-4">
                <nav class="flex items-center gap-4 w-full">
                    <div class="flex gap-1 bg-transparent rounded-lg p-1">
                        <button on:click={() => gotoTab(1)} class={setupTab===1 ? 'px-4 py-2 rounded-md text-sm font-medium transition bg-white text-blue-700 shadow-sm' : 'px-4 py-2 rounded-md text-sm font-medium transition text-gray-600 hover:bg-gray-100'} aria-pressed={setupTab===1}>
                            <span class="mr-2 font-semibold text-xs">1</span>
                            <span class="text-sm">Select / Add</span>
                        </button>
                        <button on:click={() => gotoTab(2)} class={setupTab===2 ? 'px-4 py-2 rounded-md text-sm font-medium transition bg-white text-blue-700 shadow-sm' : 'px-4 py-2 rounded-md text-sm font-medium transition text-gray-600 hover:bg-gray-100'} aria-pressed={setupTab===2}>
                            <span class="mr-2 font-semibold text-xs">2</span>
                            <span class="text-sm">Snapshot & Draw</span>
                        </button>
                        <button on:click={() => gotoTab(3)} class={setupTab===3 ? 'px-4 py-2 rounded-md text-sm font-medium transition bg-white text-blue-700 shadow-sm' : 'px-4 py-2 rounded-md text-sm font-medium transition text-gray-600 hover:bg-gray-100'} aria-pressed={setupTab===3}>
                            <span class="mr-2 font-semibold text-xs">3</span>
                            <span class="text-sm">Summary & Start</span>
                        </button>
                    </div>
                </nav>
            </div>

            <!-- Tab panels -->
            {#if setupTab === 1}
                <div class="grid grid-cols-1 gap-6">
                    <div class="bg-gray-50 rounded-lg border border-gray-200 p-4">
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="font-semibold text-gray-700">Existing Setups</h3>
                            <button class="text-sm text-blue-600 hover:underline" on:click={loadSetups}>Refresh</button>
                        </div>
                        {#if setups.length > 0}
                            <ul class="space-y-2 max-h-64 overflow-auto">
                                {#each setups as s}
                                    <li class="p-2 bg-white rounded border flex items-center justify-between">
                                        <div>
                                            <div class="font-medium text-gray-800">{s.location}</div>
                                            <div class="text-xs text-gray-500">Zones: {s.zones?.length || 0} • {s.created_at}</div>
                                        </div>
                                        <div class="flex gap-2">
                                            <button class="text-sm px-2 py-1 rounded bg-gray-100 hover:bg-gray-200" on:click={() => { newSetup = { location: s.location, zones: s.zones || [] }; gotoTab(2); }}>Load & Edit</button>
                                        </div>
                                    </li>
                                {/each}
                            </ul>
                        {:else}
                            <div class="text-sm text-gray-500">No setups yet.</div>
                        {/if}
                    </div>

                    <div class="bg-gray-50 rounded-lg border border-gray-200 p-4">
                        <h3 class="font-semibold text-gray-700 mb-3">Create New Setup</h3>
                        <label class="block text-sm text-gray-600 mb-1" for="locationNameInput">Location name</label>
                        <input id="locationNameInput" type="text" class="w-full border rounded px-3 py-2 mb-3" bind:value={newSetup.location} placeholder="e.g., Warehouse A" />
                        <div class="flex gap-2">
                            <button class="px-3 py-2 rounded bg-blue-600 text-white" on:click={() => { if (newSetup.location) gotoTab(2); else alert('Enter a name first'); }}>Next: Snapshot</button>
                            <button class="px-3 py-2 rounded bg-gray-200" on:click={() => { newSetup = { location: '', zones: [] }; snapshotURL = null; }}>Reset</button>
                        </div>
                    </div>
                </div>
            {/if}

            {#if setupTab === 2}
                <div class="grid grid-cols-1 gap-6">
                    <div class="bg-gray-50 rounded-lg border border-gray-200 p-4 flex flex-col" style="min-height:520px;">
                        <h3 class="font-semibold text-gray-700 mb-3">Snapshot</h3>
                        <div class="flex items-center gap-2 mb-3">
                            <button class="px-3 py-2 rounded bg-blue-600 text-white" on:click={fetchSnapshot} disabled={!newSetup.location || loading}>Request Snapshot</button>
                            {#if snapshotURL}
                                <span class="text-xs text-gray-600">Snapshot ready</span>
                            {/if}
                            <div class="ml-auto">
                                <button class="px-3 py-2 rounded bg-gray-200" on:click={() => gotoTab(1)}>Back</button>
                                <button class="px-3 py-2 rounded bg-green-600 text-white ml-2" on:click={() => gotoTab(3)} disabled={!snapshotURL}>Next: Summary</button>
                            </div>
                        </div>
                        {#if snapshotURL}
                            <div class="w-full flex-1 flex items-center justify-center" style="max-width:1200px;">
                                <!-- Large ZoneDrawer like the main Draw Zones modal; set explicit height to avoid clipping -->
                                <div class="w-full" style="height:520px; max-height:70vh; overflow:auto;">
                                    <ZoneDrawer onFinishZone={addNewSetupZone} width={1200} height={675} zones={newSetup.zones} showZones={true} imageSrc={snapshotURL} />
                                </div>
                            </div>
                        {:else}
                            <div class="text-sm text-gray-500">No snapshot yet. Click Request Snapshot to use the static snapshot when server is unavailable.</div>
                        {/if}
                    </div>
                </div>
            {/if}

            {#if setupTab === 3}
                <div class="grid grid-cols-1 gap-6">
                    <div class="bg-gray-50 rounded-lg border border-gray-200 p-4" style="min-height:520px;">
                        <h3 class="font-semibold text-gray-700 mb-3">Summary</h3>
                        <div class="mb-3">
                            <div class="text-sm text-gray-600">Location</div>
                            <div class="font-medium">{newSetup.location}</div>
                        </div>
                        <div class="mb-3 flex-1">
                            <div class="text-sm text-gray-600">Snapshot</div>
                            {#if snapshotURL}
                                <div class="mt-2 h-[420px] max-h-[70vh] overflow-auto">
                                        <!-- Read-only preview that shows zones correctly -->
                                        <ZoneDrawer onFinishZone={() => {}} width={1200} height={675} zones={newSetup.zones} showZones={true} imageSrc={snapshotURL} readOnly={true} />
                                    </div>
                            {:else}
                                <div class="text-sm text-gray-500">No snapshot available.</div>
                            {/if}
                        </div>
                        <div class="flex items-center gap-2">
                            <button class="px-3 py-2 rounded bg-gray-200" on:click={() => gotoTab(2)}>Back</button>
                            <button class="ml-auto px-3 py-2 rounded bg-green-600 text-white" on:click={startSetup} disabled={newSetup.zones.length === 0}>Start</button>
                        </div>
                    </div>
                </div>
            {/if}
        </div>
    </Modal>
</main>

<style>
    :global(body) {
        background: #f9fafb;
    }
</style>

<!-- <h1>Events</h1>

{#if events.length > 0}
    <ul>
    {#each events as e}
        <li>
            <span>{e.message}</span>
        </li>
    {/each}
    </ul>
{:else}
    <p>No events yet</p>
{/if} -->


<!-- <ZoneDrawer onFinishZone={sendZone} />
 -->
<!-- <div class="grid grid-cols-2 gap-4 p-4 bg-gray-100 min-h-screen">
  <div class="card col-span-2"><TablePlaceholder /></div>
  <div class="card col-span-2"><TablePlaceholder /></div>
  <div class="card col-span-2"><TablePlaceholder /></div>
</div> -->

<!-- <div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
  <div class="bg-white rounded-lg shadow p-4 h-80">
    <LineChart />
  </div>
</div> -->

<!-- <div class="p-4 space-y-4">
  <button
    on:click={fetchSnapshot}
    class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
    disabled={loading}>
    {#if loading} Loading... {/if}
    {#if !loading} Take Snapshot {/if}
  </button>

  {#if error}
    <p class="text-red-600">Error: {error}</p>
  {/if}

  {#if snapshotURL}
    <div class="mt-4">
      <img src={snapshotURL} alt="Camera snapshot" class="max-w-full rounded shadow" />
    </div>
  {/if}
</div>
<div class="p-4 space-y-4">
  <button
    on:click={loadEvents}
    class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
    disabled={loading}>
    {#if loading} Loading... {/if}
    {#if !loading} Load Events {/if}
  </button>

  {#if error}
    <p class="text-red-600">Error: {error}</p>
  {/if}

  {#if events.length > 0}
    <ul class="mt-4 space-y-2">
      {#each events as e}
        <li class="p-2 bg-white rounded shadow">{e.message}</li>
      {/each}
    </ul>
  {:else}
    <p class="mt-4">No events yet</p>
  {/if}
</div> -->
