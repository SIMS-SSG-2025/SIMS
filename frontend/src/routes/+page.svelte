
<script lang="ts">
    import TablePlaceholder from "$lib/components/TablePlaceholder.svelte";
    import LineChart from "$lib/components/LineChart.svelte";
    import ZoneDrawer from "$lib/components/ZoneDrawer.svelte";
    import Modal from "$lib/components/modal.svelte";
    import { onMount } from "svelte";

    let now = new Date();
    let interval: any;
    let selectedRange: "day" | "week" | "month" | "all" = "day";

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

    function openZoneModal() {
        showZoneModal = true;
    }
    function closeZoneModal() {
        showZoneModal = false;
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

    async function fetchSnapshot() {
        loading = true;
        error = null;
        try {
            const response = await fetch("http://10.10.67.44:8000/snapshot");
            if (!response.ok) {
                throw new Error(`Error fetching snapshot: ${response.statusText}`);
            }
            const blob = await response.blob();
            snapshotURL = URL.createObjectURL(blob);
        } catch (err: any) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

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

    async function sendZone(points: { x: number; y: number }[], name: string) {
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
            const response = await fetch("http://10.10.67.44:8000/logs");
            if (!response.ok) {
                throw new Error(`Error fetching logs: ${response.statusText}`);
            }
            const logs = await response.json();
            console.log(logs);
        } catch (err: any) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

</script>

<header class="w-full bg-white shadow flex items-center justify-between px-8 py-4">
    <!-- Left: Date & Time -->
    <div class="flex items-center min-w-[180px]">
        <span class="text-gray-700 font-mono text-lg select-none">
            {now.toLocaleDateString()} {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
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
        <button class="p-2 rounded-full hover:bg-gray-100 transition" aria-label="Export">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
        </button>
        <button class="p-2 rounded-full hover:bg-gray-100 transition" aria-label="Settings">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6l4 2" />
            </svg>
        </button>
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
            <span class="text-2xl font-bold text-gray-800 mb-2">Log Messages</span>
            <button on:click={fetchLogs} class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-full font-semibold shadow hover:bg-blue-700 transition">
                Fetch Logs
            </button>
            <div class="flex-1 w-full max-h-32 overflow-y-auto text-sm text-gray-700 bg-gray-50 rounded p-2 border border-gray-200">
                <!-- Placeholder for log messages -->
                <div>No log messages yet.</div>
            </div>
        </div>
    </div>

    <Modal open={showZoneModal} onClose={closeZoneModal} modalClass="p-0 w-full max-w-6xl max-h-[95vh]">
        <span class="text-lg font-semibold text-gray-700 mb-2 mt-6">Draw Zones on Snapshot</span>
        <div class="flex flex-col items-center p-6 w-full">
            <div class="w-full" style="max-width:1200px;">
                <ZoneDrawer onFinishZone={sendZone} width={1200} height={675} />
            </div>
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
