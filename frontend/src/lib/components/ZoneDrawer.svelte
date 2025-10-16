<script lang="ts">
    export let onFinishZone: (points: { x: number; y: number }[], name: string) => void;
    export let width: number = 640;
    export let height: number = 360;
    export let zones: { points: { x: number; y: number }[], name: string }[] = [];
    export let imageSrc: string = '/snapshot.jpg';
    export let readOnly: boolean = false;

    // Internal state - managed by ZoneDrawer itself
    let showZones = true;
    import { onMount } from "svelte";    interface Point {
        x: number;
        y: number;
    }
    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D;
    let img: HTMLImageElement;
    let container: HTMLDivElement;
    let renderedWidth = width;
    let renderedHeight = height;
    let drawing: boolean = false;
    let points: Point[] = [];
    let draggingPointsIndex: number | null = null;
    let imageAspectRatio = width / height; // Default aspect ratio

    let showNameInput = false;
    let newZoneName: string = "";

    onMount(() => {
        // Only initialize canvas for interactive mode
        if (!readOnly) {
            ctx = canvas.getContext("2d")!;
        }

        img = new Image();
        img.src = imageSrc;
        img.onload = () => {
            // Update aspect ratio based on actual image dimensions
            imageAspectRatio = img.width / img.height;
            if (!readOnly) {
                updateCanvasSize();
                drawImageContained();
            }
        };

        if (!readOnly) {
            window.addEventListener('resize', updateCanvasSize);
        }

        return () => {
            if (!readOnly) {
                window.removeEventListener('resize', updateCanvasSize);
            }
        };
    })

    function updateCanvasSize() {
        if (container && img) {
            // Get the container's size (which matches the image's rendered size)
            renderedWidth = container.clientWidth;
            renderedHeight = container.clientHeight;
            canvas.width = renderedWidth;
            canvas.height = renderedHeight;
            drawImageContained();
            redraw();
        }
    }

    function drawImageContained() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (!img.complete) return;
        // Fill the entire canvas with the image while maintaining aspect ratio
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }    function getMousePos(event: MouseEvent): Point {
        const rect = canvas.getBoundingClientRect();
        // Map mouse position to canvas coordinates
        return {
            x: (event.clientX - rect.left) * (canvas.width / rect.width),
            y: (event.clientY - rect.top) * (canvas.height / rect.height)
        };
    }

    function findPointIndex(pos: Point): number {
        return points.findIndex((pt) => Math.hypot(pt.x - pos.x, pt.y - pos.y) < 6);
    }

    function handleMouseDown(event: MouseEvent): void {
        if (readOnly) return;
        const pos = getMousePos(event);
        const idx = findPointIndex(pos);
        if (idx !== -1) {
            draggingPointsIndex = idx;
        }
    }

    function handleMouseMove(event: MouseEvent): void {
        if (readOnly) return;
        const pos = getMousePos(event);
        const idx = findPointIndex(pos);
        if (draggingPointsIndex !== null) {
            const pos = getMousePos(event);
            points[draggingPointsIndex] = pos;
            redraw();
        }
        if (canvas) {
            canvas.style.cursor = idx !== -1 ? "pointer" : "crosshair";
        }
    }

    function handleMouseUp(): void {
        if (readOnly) return;
        if (draggingPointsIndex !== null) {
            points = orderPolygonPoints(points);
            redraw();
        }
        draggingPointsIndex = null;
    }

    function handleClick(event: MouseEvent): void {
        if (readOnly) return;
        const pos = getMousePos(event);
        // Only add a point if not clicking on an existing point
        if (findPointIndex(pos) !== -1) return;
        points = [...points, {x: pos.x, y: pos.y}];
        points = orderPolygonPoints(points);
        console.log(points);
        redraw();
    }

    function handleUndo(): void {
        if (readOnly) return;
        points.pop();
        console.log(points);
        showNameInput = false;
        redraw();
    }

    function handleFinish(): void {
        if (readOnly) return;
        if(points.length > 2) {
            showNameInput = true;
            newZoneName = "";
        }
        else {
            alert("A zone must have at least 3 points.");
        }

    }

    function saveZone() {
        if (readOnly) return;
        const normalizedPoints = points.map(p => ({
            x: p.x / canvas.width,
            y: p.y / canvas.height
        }));
        console.log("Zone JSON:", JSON.stringify({ points: normalizedPoints }));
        onFinishZone(normalizedPoints, newZoneName || `Zone ${zones.length + 1}`);
        points = [];
        showNameInput = false;
        redraw();
    }

    // Zone management functions (moved from parent)
    function toggleZones() {
        showZones = !showZones;
        redraw();
    }

    function removeZone(index: number) {
        zones = zones.filter((_, i) => i !== index);
        redraw();
    }

    function orderPolygonPoints(points: Point[]): Point[] {
        const cx = points.reduce((sum, p) => sum + p.x, 0) / points.length;
        const cy = points.reduce((sum, p) => sum + p.y, 0) / points.length;
        return [...points].sort((a, b) => {
            const angleA = Math.atan2(a.y - cy, a.x - cx);
            const angleB = Math.atan2(b.y - cy, b.x - cx);
            return angleA - angleB;
        });
    }

    function redraw(): void {
        drawImageContained();

        // Always draw existing zones first
        if (showZones && zones && zones.length > 0) {
            zones.forEach(zone => {
                if (zone.points.length >= 3) {
                    ctx.beginPath();
                    ctx.moveTo(zone.points[0].x * canvas.width, zone.points[0].y * canvas.height);
                    for (let i = 1; i < zone.points.length; i++) {
                        ctx.lineTo(zone.points[i].x * canvas.width, zone.points[i].y * canvas.height);
                    }
                    ctx.closePath();
                    ctx.fillStyle = "rgba(0, 123, 255, 0.15)";
                    ctx.fill();
                    ctx.strokeStyle = "rgba(0, 123, 255, 0.7)";
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            });
        }

        // Then draw current drawing points (only in non-readonly mode)
        if (!readOnly && points.length > 0) {
            // Draw filled polygon if 3+ points
            if (points.length >= 3) {
                ctx.beginPath();
                ctx.moveTo(points[0].x, points[0].y);
                for (let i = 1; i < points.length; i++) {
                    ctx.lineTo(points[i].x, points[i].y);
                }
                ctx.closePath();
                ctx.fillStyle = "rgba(255, 0, 0, 0.3)";
                ctx.fill();

                ctx.strokeStyle = "red";
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // Draw small blue circles at each point
            points.forEach((pt) => {
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
                ctx.fillStyle = "blue";
                ctx.fill();
            });
        }
    }

    // Reactive statement to redraw when zones change (only for canvas mode)
    $: if (!readOnly && ctx && img) {
        redraw();
    }

    // Specific reactive statement for zones changes in canvas mode
    $: if (!readOnly && ctx && img && zones) {
        redraw();
    }

    // Handle visibility changes - recalculate canvas when becoming visible
    $: if (!readOnly && container && ctx && img) {
        // Small delay to ensure DOM is ready after tab switch
        setTimeout(() => {
            updateCanvasSize();
        }, 10);
    }
</script>

<div class="flex flex-col">
    {#if !readOnly}
        <!-- Control Panel -->
        <div class="bg-white border border-gray-100 p-3 mb-3 shadow-sm">
            <!-- Top Row: Zone visibility and drawing controls -->
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                    <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium rounded border border-gray-200 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors"
                        on:click={toggleZones}
                    >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={showZones ? "M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" : "M12 6v6m0 0v6m0-6h6m-6 0H6"}></path>
                        </svg>
                        {showZones ? "Hide" : "Show"}
                    </button>
                    <span class="text-xs text-gray-500">
                        {zones.length} zone{zones.length !== 1 ? 's' : ''}
                    </span>
                </div>

                <div class="flex items-center gap-1">
                    <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium rounded border border-gray-200 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors disabled:opacity-50"
                        on:click={handleUndo}
                        disabled={points.length === 0}
                        aria-label="Undo last point"
                        type="button"
                    >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"></path>
                        </svg>
                        Undo
                    </button>
                    <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-blue-500 text-white hover:bg-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        on:click={handleFinish}
                        disabled={points.length < 3}
                        aria-label="Finish zone"
                        type="button"
                    >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        Finish
                    </button>
                </div>
            </div>

            <!-- Zone Name Input (appears when finishing zone) -->
            {#if showNameInput}
                <div class="flex items-center gap-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                    <input
                        type="text"
                        bind:value={newZoneName}
                        placeholder="Zone name..."
                        class="flex-1 px-2 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-transparent"
                        on:keydown={(e) => { if (e.key === 'Enter') saveZone(); }}
                        autofocus
                    />
                    <button
                        class="px-2 py-1 text-xs font-medium rounded bg-blue-500 text-white hover:bg-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors"
                        on:click={saveZone}
                    >
                        Save
                    </button>
                </div>
            {/if}

            <!-- Existing Zones List -->
            {#if zones.length > 0}
                <div class="border-t border-gray-100 pt-2 mt-2">
                    <div class="flex flex-wrap gap-1">
                        {#each zones as zone, i}
                            <div class="inline-flex items-center bg-blue-50 text-blue-700 rounded px-2 py-0.5 text-xs border border-blue-100">
                                <span class="mr-1">{zone.name || `Zone ${i + 1}`}</span>
                                <button
                                    class="text-blue-500 hover:text-red-500 focus:outline-none transition-colors"
                                    title="Remove zone"
                                    on:click={() => removeZone(i)}
                                >
                                    <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                    </svg>
                                </button>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    {/if}

    <!-- Canvas Container -->
    <div bind:this={container} class="relative w-full h-auto overflow-hidden" style="aspect-ratio: {imageAspectRatio}; max-width: 100%;">
        <img src={imageSrc} alt="Snapshot" class="absolute inset-0 w-full h-full object-fill pointer-events-none select-none" draggable="false" style="z-index:1;" />

        {#if readOnly}
            <!-- SVG overlay for read-only mode -->
            <svg class="absolute inset-0 w-full h-full pointer-events-none" style="z-index:2;" viewBox="0 0 100 100" preserveAspectRatio="none">
                {#if showZones && zones && zones.length > 0}
                    {#each zones as zone}
                        {#if zone.points.length >= 3}
                            <polygon
                                points={zone.points.map(p => `${p.x * 100},${p.y * 100}`).join(' ')}
                                fill="rgba(255, 30, 0, 0.3)"
                                stroke="rgba(255, 0, 0, 0.7)"
                                stroke-width="0.4"
                                vector-effect="non-scaling-stroke"
                            />
                        {/if}
                    {/each}
                {/if}
            </svg>
        {:else}
            <!-- Canvas for interactive mode -->
            <canvas
                bind:this={canvas}
                width={renderedWidth}
                height={renderedHeight}
                on:click={handleClick}
                on:mousedown={handleMouseDown}
                on:mousemove={handleMouseMove}
                on:mouseup={handleMouseUp}
                class="absolute inset-0"
                style="cursor: crosshair; width: 100%; height: 100%; background: transparent; z-index:2;"
            ></canvas>
        {/if}
    </div>
</div>
