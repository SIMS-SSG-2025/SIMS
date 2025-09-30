<script lang="ts">
    import TablePlaceholder from "$lib/components/TablePlaceholder.svelte";
    import LineChart from "$lib/components/LineChart.svelte";
    import ZoneDrawer from "$lib/components/ZoneDrawer.svelte";
    import { onMount } from "svelte";

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
</script>

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


<ZoneDrawer />

<!-- <div class="grid grid-cols-2 gap-4 p-4 bg-gray-100 min-h-screen">
  <div class="card col-span-2"><TablePlaceholder /></div>
  <div class="card col-span-2"><TablePlaceholder /></div>
  <div class="card col-span-2"><TablePlaceholder /></div>
</div> -->

<div class="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
  <div class="bg-white rounded-lg shadow p-4 h-80">
    <LineChart />
  </div>
  <!-- other cards/placeholders -->
</div>

<div class="p-4 space-y-4">
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
</div>
