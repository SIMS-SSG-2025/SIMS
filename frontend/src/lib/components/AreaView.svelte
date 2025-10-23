<script lang="ts">
    import { onMount } from 'svelte';
    import { fetchObjectPositions, type ObjectPosition, type Zone } from '$lib/api/config';
    import { Layers, Activity } from 'lucide-svelte';
    // @ts-ignore - heatmap.js doesn't have TypeScript definitions
    import h337 from 'heatmap.js';

    // Props using Svelte 5 $props()
    let {
        locationId,
        zones = [],
        imageSrc
    }: {
        locationId: number;
        zones?: Zone[];
        imageSrc: string;
    } = $props();

    // State
    let viewMode = $state<'zones' | 'heatmap'>('zones'); // Toggle between zones and heatmap
    let selectedDate = $state(new Date().toISOString().split('T')[0]); // YYYY-MM-DD format
    let loading = $state(false);
    let heatmapInstance = $state<any>(null);
    let container = $state<HTMLDivElement>();
    let heatmapContainer = $state<HTMLDivElement>(); // Separate container for heatmap canvas
    let img = $state<HTMLImageElement>();
    let positions = $state<ObjectPosition[]>([]);
    let imageLoaded = $state(false);
    let imageWidth = $state(1920);
    let imageHeight = $state(1080);

    // Computed
    let positionCount = $derived(positions.length);
    let showZones = $derived(viewMode === 'zones');
    let showHeatmap = $derived(viewMode === 'heatmap');

    onMount(() => {
        img = new Image();
        img.src = imageSrc;
        img.onload = () => {
            if (img) {
                imageWidth = img.naturalWidth;
                imageHeight = img.naturalHeight;
                imageLoaded = true;
            }
        };
    });

    // Initialize heatmap when switching to heatmap view
    $effect(() => {
        if (viewMode === 'heatmap' && heatmapContainer && !heatmapInstance && imageLoaded) {
            initializeHeatmap();
        }
    });

    function initializeHeatmap() {
        if (!heatmapContainer || heatmapInstance) return;

        // Create heatmap instance on the separate heatmap container
        heatmapInstance = h337.create({
            container: heatmapContainer,
            radius: 25,
            maxOpacity: 0.6,
            minOpacity: 0.1,
            blur: 0.75,
            gradient: {
                '0.0': 'blue',
                '0.5': 'cyan',
                '0.7': 'lime',
                '0.8': 'yellow',
                '1.0': 'red'
            }
        });

        // Set initial visibility based on current mode
        updateHeatmapVisibility();
    }

    async function loadHeatmapData() {
        if (!selectedDate) return;

        loading = true;
        try {
            // Fetch positions for the selected date (start and end are the same for single day)
            const data = await fetchObjectPositions(locationId, selectedDate, selectedDate);
            positions = data;

            if (heatmapInstance && container) {
                const containerWidth = container.clientWidth;
                const containerHeight = container.clientHeight;

                // Convert normalized positions (0-1) to pixel coordinates
                const heatmapData = data.map(pos => ({
                    x: Math.round(pos.x * containerWidth),
                    y: Math.round(pos.y * containerHeight),
                    value: 1
                }));

                // Update heatmap
                heatmapInstance.setData({
                    max: 10,
                    data: heatmapData
                });
            }
        } catch (error) {
            console.error('Error loading heatmap data:', error);
        } finally {
            loading = false;
        }
    }

    function clearHeatmap() {
        if (heatmapInstance) {
            heatmapInstance.setData({ max: 0, data: [] });
        }
        positions = [];
    }

    function updateHeatmapVisibility() {
        if (!heatmapContainer) return;

        // Toggle visibility of the heatmap container itself
        if (heatmapContainer) {
            heatmapContainer.style.display = showHeatmap ? 'block' : 'none';
        }
    }

    function switchToZones() {
        viewMode = 'zones';
        updateHeatmapVisibility();
    }

    function switchToHeatmap() {
        viewMode = 'heatmap';
        // Initialize heatmap if not already done
        if (imageLoaded && !heatmapInstance && heatmapContainer) {
            initializeHeatmap();
        }
        updateHeatmapVisibility();
    }

    // Update heatmap visibility when view mode changes
    $effect(() => {
        if (heatmapInstance) {
            updateHeatmapVisibility();
        }
    });
</script>

<div class="flex flex-col gap-3">
    <!-- Compact Header with Toggle and Controls -->
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div class="px-4 py-3 flex items-center justify-between gap-4 border-b border-gray-100">
            <!-- Left: Title and Toggle -->
            <div class="flex items-center gap-4">
                <h3 class="text-base font-semibold text-gray-900">Camera View</h3>

                <!-- View Mode Toggle -->
                <div class="inline-flex rounded-lg border border-gray-200 p-0.5 bg-gray-50">
                    <button
                        onclick={switchToZones}
                        class={`
                            px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5
                            ${showZones ? 'bg-white text-[#E76A23] shadow-sm' : 'text-gray-600 hover:text-gray-900'}
                        `}
                    >
                        <Layers class="w-3.5 h-3.5" />
                        Zones
                    </button>
                    <button
                        onclick={switchToHeatmap}
                        class={`
                            px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5
                            ${showHeatmap ? 'bg-white text-[#E76A23] shadow-sm' : 'text-gray-600 hover:text-gray-900'}
                        `}
                    >
                        <Activity class="w-3.5 h-3.5" />
                        Heatmap
                    </button>
                </div>
            </div>

            <!-- Right: Heatmap Controls (compact, inline) -->
            {#if showHeatmap}
                <div class="flex items-center gap-2">
                    <!-- Date Picker -->
                    <div class="relative">
                        <input
                            id="heatmap-date"
                            type="date"
                            bind:value={selectedDate}
                            max={new Date().toISOString().split('T')[0]}
                            class="px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-[#E76A23] focus:border-transparent"
                        />
                    </div>

                    <!-- Load Button -->
                    <button
                        onclick={loadHeatmapData}
                        disabled={loading || !selectedDate}
                        class="px-3 py-1.5 bg-[#E76A23] text-white rounded text-xs font-medium hover:bg-[#d15e1e] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                        {loading ? 'Loading...' : 'Load'}
                    </button>

                    <!-- Clear Button -->
                    <button
                        onclick={clearHeatmap}
                        disabled={positions.length === 0}
                        class="px-3 py-1.5 bg-gray-500 text-white rounded text-xs font-medium hover:bg-gray-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                        Clear
                    </button>

                    <!-- Position Count Badge -->
                    {#if positionCount > 0}
                        <div class="px-2 py-1 bg-[#E76A23] bg-opacity-10 text-[#E76A23] rounded text-xs font-medium">
                            {positionCount} positions
                        </div>
                    {/if}

                    <!-- Mini Legend -->
                    {#if positionCount > 0}
                        <div class="flex items-center gap-1.5 pl-2 border-l border-gray-200">
                            <span class="text-xs text-gray-500">Activity:</span>
                            <div class="w-20 h-2 rounded" style="background: linear-gradient(to right, blue, cyan, lime, yellow, red);"></div>
                        </div>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- Compact Visualization Area -->
        <div class="px-4 pb-4">
            <div class="relative w-full" style="padding-bottom: 56.25%; /* 16:9 aspect ratio */">
                <div
                    bind:this={container}
                    class="absolute inset-0 flex items-center justify-center bg-gray-100 rounded overflow-hidden"
                >
                {#if imageLoaded}
                    <!-- Base Image -->
                    <img
                        src={imageSrc}
                        alt="Camera snapshot"
                        class="absolute inset-0 w-full h-full object-contain"
                        style="z-index: 1;"
                    />

                    <!-- Zones Overlay (SVG) - only show in zones mode -->
                    {#if showZones && zones.length > 0}
                        <svg
                            class="absolute inset-0 w-full h-full"
                            style="z-index: 2;"
                            viewBox="0 0 {imageWidth} {imageHeight}"
                            preserveAspectRatio="xMidYMid meet"
                        >
                            {#each zones as zone, idx}
                                <g>
                                    <!-- Zone polygon -->
                                    <polygon
                                        points={zone.points.map((coord: { x: number; y: number }) => `${coord.x * imageWidth},${coord.y * imageHeight}`).join(' ')}
                                        fill="rgba(231, 106, 35, 0.3)"
                                        stroke="#E76A23"
                                        stroke-width="3"
                                    />
                                    <!-- Zone label -->
                                    {#if zone.points.length > 0}
                                        {@const centerX = zone.points.reduce((sum: number, coord: { x: number; y: number }) => sum + coord.x, 0) / zone.points.length * imageWidth}
                                        {@const centerY = zone.points.reduce((sum: number, coord: { x: number; y: number }) => sum + coord.y, 0) / zone.points.length * imageHeight}
                                        <text
                                            x={centerX}
                                            y={centerY}
                                            text-anchor="middle"
                                            dominant-baseline="middle"
                                            fill="rgba(231, 106, 35, 0.8)"
                                            font-size="24"
                                            font-weight="bold"
                                        >
                                            {zone.name}
                                        </text>
                                    {/if}
                                </g>
                            {/each}
                        </svg>
                    {/if}

                    <!-- Heatmap Canvas - only show in heatmap mode -->
                    {#if showHeatmap}
                        <!-- Zones as subtle background in heatmap mode -->
                        {#if zones.length > 0}
                            <svg
                                class="absolute inset-0 w-full h-full"
                                style="z-index: 2; opacity: 0.3;"
                                viewBox="0 0 {imageWidth} {imageHeight}"
                                preserveAspectRatio="xMidYMid meet"
                            >
                                {#each zones as zone}
                                    <polygon
                                        points={zone.points.map((coord: { x: number; y: number }) => `${coord.x * imageWidth},${coord.y * imageHeight}`).join(' ')}
                                        fill="none"
                                        stroke="#E76A23"
                                        stroke-width="2"
                                        stroke-dasharray="5,5"
                                    />
                                    {#if zone.points.length > 0}
                                        {@const centerX = zone.points.reduce((sum: number, coord: { x: number; y: number }) => sum + coord.x, 0) / zone.points.length * imageWidth}
                                        {@const centerY = zone.points.reduce((sum: number, coord: { x: number; y: number }) => sum + coord.y, 0) / zone.points.length * imageHeight}
                                        <text
                                            x={centerX}
                                            y={centerY}
                                            text-anchor="middle"
                                            dominant-baseline="middle"
                                            fill="rgba(231, 106, 35, 0.8)"
                                            font-size="24"
                                            font-weight="bold"
                                        >
                                            {zone.name}
                                        </text>
                                    {/if}
                                {/each}
                            </svg>
                        {/if}
                        <!-- Heatmap container - h337.create() will append canvas here -->
                        <div
                            bind:this={heatmapContainer}
                            class="absolute inset-0"
                            style="z-index: 3; pointer-events: none;"
                        ></div>
                    {/if}

                    <!-- Loading Overlay -->
                    {#if loading}
                        <div class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center" style="z-index: 10;">
                            <div class="bg-white rounded-lg p-4 shadow-lg">
                                <div class="flex items-center gap-3">
                                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#E76A23]"></div>
                                    <span class="text-gray-700 font-medium">Loading heatmap data...</span>
                                </div>
                            </div>
                        </div>
                    {/if}
                {:else}
                    <div class="text-gray-400">Loading image...</div>
                {/if}
            </div>
        </div>
        </div>
    </div>
</div>

<style>
    /* Ensure heatmap canvas is properly positioned and transparent */
    :global(.heatmap-canvas) {
        position: absolute !important;
        inset: 0;
        z-index: 3 !important;
        pointer-events: none !important;
        background: transparent !important;
    }
</style>
