<script lang="ts">
    import { Eye, EyeOff, Undo, Check, X } from 'lucide-svelte';
    import { onMount } from "svelte";

    interface Point {
        x: number;
        y: number;
    }

    // Props
    let {
        onFinishZone,
        width = 640,
        height = 360,
        zones = $bindable([]),
        imageSrc = '/snapshot.jpg',
        readOnly = false,
        hideControls = false,
        currentPoints = $bindable([])
    }: {
        onFinishZone: (points: { x: number; y: number }[], name: string) => void;
        width?: number;
        height?: number;
        zones?: { points: { x: number; y: number }[], name: string }[];
        imageSrc?: string;
        readOnly?: boolean;
        hideControls?: boolean;
        currentPoints?: { x: number; y: number }[];
    } = $props();

    let showZones = $state(true);
    let canvas = $state<HTMLCanvasElement>();
    let ctx = $state<CanvasRenderingContext2D>();
    let img = $state<HTMLImageElement>();
    let container = $state<HTMLDivElement>();
    let renderedWidth = $state(width);
    let renderedHeight = $state(height);
    let points = $state<Point[]>([]);
    let draggingPointsIndex = $state<number | null>(null);
    let imageAspectRatio = $state(width / height);
    let showNameInput = $state(false);
    let newZoneName = $state("");
    let helperFaded = $state(false);

    // Sync internal points with exported currentPoints using $effect
    $effect(() => {
        currentPoints = points;
    });

    // Redraw effects
    $effect(() => {
        if (!readOnly && ctx && img) {
            redraw();
        }
    });

    $effect(() => {
        if (!readOnly && ctx && img && zones) {
            redraw();
        }
    });

    $effect(() => {
        if (!readOnly && container && ctx && img) {
            setTimeout(() => {
                updateCanvasSize();
            }, 10);
        }
    });

    // Public function to finish zone from external button
    export function finishZoneFromExternal() {
        if (readOnly || points.length < 3) return;
        const normalizedPoints = points.map(p => ({
            x: p.x / canvas!.width,
            y: p.y / canvas!.height
        }));
        onFinishZone(normalizedPoints, "");
        points = [];
        redraw();
    }

    onMount(() => {
        if (!readOnly && canvas) {
            ctx = canvas.getContext("2d")!;
        }

        img = new Image();
        img.src = imageSrc;
        img.onload = () => {
            imageAspectRatio = img!.width / img!.height;
            if (!readOnly) {
                updateCanvasSize();
                drawImageContained();
            }
        };

        if (!readOnly) {
            window.addEventListener('resize', updateCanvasSize);
            window.addEventListener('keydown', handleKeyDown);
        }

        return () => {
            if (!readOnly) {
                window.removeEventListener('resize', updateCanvasSize);
                window.removeEventListener('keydown', handleKeyDown);
            }
        };
    });

    function updateCanvasSize() {
        if (container && img && canvas) {
            renderedWidth = container.clientWidth;
            renderedHeight = container.clientHeight;
            canvas.width = renderedWidth;
            canvas.height = renderedHeight;
            drawImageContained();
            redraw();
        }
    }

    function drawImageContained() {
        if (!ctx || !canvas) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (!img?.complete) return;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }

    function getMousePos(event: MouseEvent): Point {
        if (!canvas) return { x: 0, y: 0 };
        const rect = canvas.getBoundingClientRect();
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
        if (readOnly || !canvas) return;

        // Check if mouse is near the helper area
        if (hideControls && points.length >= 3) {
            const rect = canvas.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;
            helperFaded = (mouseX < 300 && mouseY < 80);
        }

        const idx = findPointIndex(getMousePos(event));
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
        if (readOnly || showNameInput) return;

        const pos = getMousePos(event);
        if (findPointIndex(pos) !== -1) return;

        points = [...points, { x: pos.x, y: pos.y }];
        points = orderPolygonPoints(points);
        redraw();
    }

    function handleUndo(): void {
        if (readOnly) return;
        points.pop();
        showNameInput = false;
        redraw();
    }

    function handleFinish(): void {
        if (readOnly) return;
        if (points.length > 2) {
            showNameInput = true;
            newZoneName = "";
        } else {
            alert("A zone must have at least 3 points.");
        }
    }

    function saveZone() {
        if (readOnly || !canvas) return;
        const normalizedPoints = points.map(p => ({
            x: p.x / canvas!.width,
            y: p.y / canvas!.height
        }));
        onFinishZone(normalizedPoints, newZoneName || `Zone ${zones.length + 1}`);
        points = [];
        showNameInput = false;
        newZoneName = "";
        redraw();
    }

    function cancelDrawing() {
        if (readOnly) return;
        points = [];
        showNameInput = false;
        newZoneName = "";
        redraw();
    }

    function handleKeyDown(event: KeyboardEvent) {
        if (!canvas) return;

        if (event.key === 'Escape') {
            cancelDrawing();
        } else if (event.key === 'Enter') {
            if (points.length >= 3) {
                const normalizedPoints = points.map(p => ({
                    x: p.x / canvas!.width,
                    y: p.y / canvas!.height
                }));
                onFinishZone(normalizedPoints, "");
                points = [];
                redraw();
            }
        }
    }

    function toggleZones() {
        showZones = !showZones;
        redraw();
    }

    function removeZone(index: number) {
        zones = zones.filter((_, i) => i !== index);
        redraw();
    }

    function orderPolygonPoints(pts: Point[]): Point[] {
        if (pts.length === 0) return pts;
        const cx = pts.reduce((sum, p) => sum + p.x, 0) / pts.length;
        const cy = pts.reduce((sum, p) => sum + p.y, 0) / pts.length;
        return [...pts].sort((a, b) => {
            const angleA = Math.atan2(a.y - cy, a.x - cx);
            const angleB = Math.atan2(b.y - cy, b.x - cx);
            return angleA - angleB;
        });
    }

    function redraw(): void {
        if (!ctx || !canvas) return;

        drawImageContained();

        // Draw existing zones
        if (showZones && zones && zones.length > 0) {
            zones.forEach(zone => {
                if (zone.points.length >= 3) {
                    ctx!.beginPath();
                    ctx!.moveTo(zone.points[0].x * canvas!.width, zone.points[0].y * canvas!.height);
                    for (let i = 1; i < zone.points.length; i++) {
                        ctx!.lineTo(zone.points[i].x * canvas!.width, zone.points[i].y * canvas!.height);
                    }
                    ctx!.closePath();
                    ctx!.fillStyle = "rgba(0, 123, 255, 0.15)";
                    ctx!.fill();
                    ctx!.strokeStyle = "rgba(0, 123, 255, 0.7)";
                    ctx!.lineWidth = 2;
                    ctx!.stroke();
                }
            });
        }

        // Draw current drawing points
        if (!readOnly && points.length > 0) {
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

            points.forEach((pt) => {
                ctx!.beginPath();
                ctx!.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
                ctx!.fillStyle = "blue";
                ctx!.fill();
            });
        }
    }
</script>

<div class="flex flex-col relative">
    {#if !readOnly && !hideControls}
        <!-- Control Panel -->
        <div class="bg-white border border-gray-100 p-3 mb-3 shadow-sm">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                    <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium rounded border border-gray-200 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors"
                        onclick={toggleZones}
                    >
                        {#if showZones}
                            <EyeOff class="w-3 h-3 mr-1" />
                            Hide
                        {:else}
                            <Eye class="w-3 h-3 mr-1" />
                            Show
                        {/if}
                    </button>
                    <span class="text-xs text-gray-500">
                        {zones.length} zone{zones.length !== 1 ? 's' : ''}
                    </span>
                </div>

                <div class="flex items-center gap-1">
                    <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium rounded border border-gray-200 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors disabled:opacity-50"
                        onclick={handleUndo}
                        disabled={points.length === 0}
                        aria-label="Undo last point"
                        type="button"
                    >
                        <Undo class="w-3 h-3 mr-1" />
                        Undo
                    </button>
                    <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-blue-500 text-white hover:bg-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        onclick={handleFinish}
                        disabled={points.length < 3}
                        aria-label="Finish zone"
                        type="button"
                    >
                        <Check class="w-3 h-3 mr-1" />
                        Finish
                    </button>
                </div>
            </div>

            <!-- Zone Name Input -->
            {#if showNameInput}
                <div class="flex items-center gap-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                    <input
                        type="text"
                        bind:value={newZoneName}
                        placeholder="Zone name..."
                        class="flex-1 px-2 py-1 border border-blue-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-400 focus:border-transparent"
                        onkeydown={(e) => { if (e.key === 'Enter') saveZone(); }}
                    />
                    <button
                        class="px-2 py-1 text-xs font-medium rounded bg-blue-500 text-white hover:bg-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-400 transition-colors"
                        onclick={saveZone}
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
                                    onclick={() => removeZone(i)}
                                >
                                    <X class="w-2.5 h-2.5" />
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
                                fill="rgba(231, 106, 35, 0.3)"
                                stroke="#E76A23"
                                stroke-width="0.4"
                                vector-effect="non-scaling-stroke"
                            />
                            {#if zone.name}
                                {@const centerX = zone.points.reduce((sum, p) => sum + p.x, 0) / zone.points.length * 100}
                                {@const centerY = zone.points.reduce((sum, p) => sum + p.y, 0) / zone.points.length * 100}
                                <text
                                    x={centerX}
                                    y={centerY}
                                    text-anchor="middle"
                                    dominant-baseline="middle"
                                    fill="#E76A23"
                                    font-size="2"
                                    font-weight="700"
                                    letter-spacing="0.05"
                                >
                                    {zone.name}
                                </text>
                            {/if}
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
                onclick={handleClick}
                onmousedown={handleMouseDown}
                onmousemove={handleMouseMove}
                onmouseup={handleMouseUp}
                class="absolute inset-0"
                style="cursor: crosshair; width: 100%; height: 100%; background: transparent; z-index:2;"
            ></canvas>

            <!-- Helper message -->
            {#if hideControls && points.length >= 3}
                <div
                    class="absolute top-4 left-4 bg-[#E76A23] text-white px-4 py-2 rounded-lg shadow-lg transition-opacity duration-200 pointer-events-none"
                    class:opacity-10={helperFaded}
                    style="z-index: 50;"
                >
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold">Press <kbd class="px-1.5 py-0.5 bg-white/20 rounded text-xs font-mono">Enter</kbd> to complete zone</span>
                    </div>
                </div>
            {/if}
        {/if}
    </div>
</div>
