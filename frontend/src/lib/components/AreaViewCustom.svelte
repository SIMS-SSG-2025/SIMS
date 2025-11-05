<script lang="ts">
    import { onMount } from 'svelte';
    import { fetchObjectPositions, type ObjectPosition, type Zone } from '$lib/api/config';
    import MovementTrails from './MovementTrails.svelte';

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
    let selectedDate = $state(new Date().toISOString().split('T')[0]);
    let loading = $state(false);
    let container = $state<HTMLDivElement>();
    let img = $state<HTMLImageElement>();
    let positions = $state<ObjectPosition[]>([]);
    let imageLoaded = $state(false);
    let imageWidth = $state(1920);
    let imageHeight = $state(1080);
    let movementTrailComponent = $state<any>(null);

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

    async function loadMovementData() {
        if (!selectedDate) return;

        loading = true;
        try {
            const fetchedPositions = await fetchObjectPositions(locationId, selectedDate, selectedDate);
            positions = fetchedPositions;
        } catch (error) {
            console.error('Error loading movement data:', error);
        } finally {
            loading = false;
        }
    }

    function clearTrails() {
        positions = [];
        if (movementTrailComponent) {
            movementTrailComponent.clear();
        }
    }
</script>

<div class="flex flex-col gap-3">
    <!-- Compact Header with Controls -->
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div class="px-4 py-3 flex items-center justify-between gap-4 border-b border-gray-100">
            <!-- Left: Title -->
            <h3 class="text-base font-semibold text-gray-900">Camera View (Zones & Movement Trails)</h3>

            <!-- Right: Movement Trail Controls (compact, inline) -->
            <div class="flex items-center gap-2">
                <!-- Date Picker -->
                <div class="relative">
                    <input
                        id="movement-date"
                        type="date"
                        bind:value={selectedDate}
                        max={new Date().toISOString().split('T')[0]}
                        class="px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-[#E76A23] focus:border-transparent"
                    />
                </div>

                <!-- Load Button -->
                <button
                    onclick={loadMovementData}
                    disabled={loading || !selectedDate}
                    class="px-3 py-1.5 bg-[#E76A23] text-white rounded text-xs font-medium hover:bg-[#d15e1e] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                    {loading ? 'Loading...' : 'Load Trails'}
                </button>

                <!-- Clear Button -->
                <button
                    onclick={clearTrails}
                    disabled={positions.length === 0}
                    class="px-3 py-1.5 bg-gray-500 text-white rounded text-xs font-medium hover:bg-gray-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                    Clear Trails
                </button>

            </div>
        </div>

        <!-- Compact Visualization Area -->
        <div class="px-4 pb-4">
            <div class="relative w-full" style="padding-bottom: 56.25%;">
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

                        <!-- Zones Overlay (SVG) - always shown but transparent -->
                        {#if zones.length > 0}
                            <svg
                                class="absolute inset-0 w-full h-full"
                                style="z-index: 2;"
                                viewBox="0 0 {imageWidth} {imageHeight}"
                                preserveAspectRatio="xMidYMid meet"
                            >
                                {#each zones as zone}
                                    <g>
                                        <!-- Zone polygon with transparency -->
                                        <polygon
                                            points={zone.points.map((coord: { x: number; y: number }) => `${coord.x * imageWidth},${coord.y * imageHeight}`).join(' ')}
                                            fill="rgba(255, 50, 35, 0.3)"
                                            stroke="rgba(255, 50, 35, 0.6)"
                                            stroke-width="2"
                                        />
                                        <!-- Zone label with transparency -->
                                        {#if zone.points.length > 0}
                                            {@const centerX = zone.points.reduce((sum: number, coord: { x: number; y: number }) => sum + coord.x, 0) / zone.points.length * imageWidth}
                                            {@const centerY = zone.points.reduce((sum: number, coord: { x: number; y: number }) => sum + coord.y, 0) / zone.points.length * imageHeight}
                                            <text
                                                x={centerX}
                                                y={centerY}
                                                text-anchor="middle"
                                                dominant-baseline="middle"
                                                fill="rgba(255, 50, 35, 1)"
                                                font-size="20"
                                                font-weight="bold"
                                            >
                                                {zone.name}
                                            </text>
                                        {/if}
                                    </g>
                                {/each}
                            </svg>
                        {/if}

                        <!-- Movement Trails Component -->
                        {#if container}
                            <MovementTrails
                                bind:this={movementTrailComponent}
                                positions={positions}
                                width={container.clientWidth}
                                height={container.clientHeight}
                                lineWidth={3}
                                opacity={0.7}
                                showPoints={true}
                            />
                        {/if}

                        <!-- Loading Overlay -->
                        {#if loading}
                            <div class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center" style="z-index: 10;">
                                <div class="bg-white rounded-lg p-4 shadow-lg">
                                    <div class="flex items-center gap-3">
                                        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-[#E76A23]"></div>
                                        <span class="text-gray-700 font-medium">Loading movement data...</span>
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
