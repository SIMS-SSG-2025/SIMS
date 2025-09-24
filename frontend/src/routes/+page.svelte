<script lang="ts">
    import ZoneDrawer from "$lib/components/ZoneDrawer.svelte";
    import { onMount } from "svelte";

   /*  type Event = {
        message: string;
    };

    let events: Event[] = [];

    async function loadEvents() {
        const response = await fetch("ip");
        events = await response.json();
    }

    onMount(() => {
        loadEvents();
    });  */
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

<h1>Draw forbidden zones</h1>

<ZoneDrawer />
