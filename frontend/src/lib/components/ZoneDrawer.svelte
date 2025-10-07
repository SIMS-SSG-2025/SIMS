<script lang="ts">
    export let onFinishZone: (points: { x: number; y: number }[], name: string) => void;
    export let width: number = 640;
    export let height: number = 360;
    export let zones: { points: { x: number; y: number }[], name: string }[] = [];
    export let showZones: boolean = true;
    import { onMount } from "svelte";

    interface Point {
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

    let showNameInput = false;
    let newZoneName: string = "";

    onMount(() => {
        ctx = canvas.getContext("2d")!;
        img = new Image();
        img.src = "/snapshot.jpg";
        img.onload = () => {
            updateCanvasSize();
            drawImageContained();
        };
        window.addEventListener('resize', updateCanvasSize);
        return () => {
            window.removeEventListener('resize', updateCanvasSize);
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
        const imgAspect = img.width / img.height;
        const canvasAspect = canvas.width / canvas.height;
        let drawWidth, drawHeight, offsetX, offsetY;
        if (imgAspect > canvasAspect) {
            drawWidth = canvas.width;
            drawHeight = canvas.width / imgAspect;
            offsetX = 0;
            offsetY = (canvas.height - drawHeight) / 2;
        } else {
            drawHeight = canvas.height;
            drawWidth = canvas.height * imgAspect;
            offsetX = (canvas.width - drawWidth) / 2;
            offsetY = 0;
        }
        ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
    }

    function getMousePos(event: MouseEvent): Point {
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
        const pos = getMousePos(event);
        const idx = findPointIndex(pos);
        if (idx !== -1) {
            draggingPointsIndex = idx;
        }
    }

    function handleMouseMove(event: MouseEvent): void {
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
        if (draggingPointsIndex !== null) {
            points = orderPolygonPoints(points);
            redraw();
        }
        draggingPointsIndex = null;
    }

    function handleClick(event: MouseEvent): void {
        const pos = getMousePos(event);
        // Only add a point if not clicking on an existing point
        if (findPointIndex(pos) !== -1) return;
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        points = [...points, {x, y}];
        points = orderPolygonPoints(points);
        console.log(points);
        redraw();
    }

    function handleUndo(): void {
        points.pop();
        console.log(points);
        showNameInput = false;
        redraw();
    }

    function handleFinish(): void {
        if(points.length > 2) {
            showNameInput = true;
            newZoneName = "";
        }
        else {
            alert("A zone must have at least 3 points.");
        }

    }

    function saveZone() {
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

        if (points.length > 0) {
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
    }

    $: if (ctx && img && showZones !== undefined && zones !== undefined) {
        redraw();
    }

</script>

<div class="flex flex-col items-center">
    <div class="flex gap-2 mt-4 mb-2">
        <button
            class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium shadow focus:outline-none focus:ring-2 focus:ring-blue-400"
            on:click={handleUndo}
            aria-label="Undo last point"
            type="button"
        >
            Undo
        </button>
        <button
            class="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium shadow focus:outline-none focus:ring-2 focus:ring-blue-400"
            on:click={handleFinish}
            aria-label="Finish zone"
            type="button"
        >
            Finish Zone
        </button>
    </div>
    {#if showNameInput}
        <div class="flex gap-2 items-center mt-2">
            <input
                type="text"
                bind:value={newZoneName}
                placeholder="Zone name"
                class="px-2 py-1 border rounded focus:outline-none"
                on:keydown={(e) => { if (e.key === 'Enter') saveZone(); }}
                autofocus
            />
            <button
                class="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                on:click={saveZone}
            >
                Save Zone
            </button>
        </div>
    {/if}
    <div bind:this={container} class="relative w-full h-auto" style="aspect-ratio: {width} / {height}; max-width: 100%;">
        <img src="/snapshot.jpg" alt="Snapshot" class="absolute inset-0 w-full h-full object-contain pointer-events-none select-none" draggable="false" style="z-index:1;" />
        <canvas
            bind:this={canvas}
            width={renderedWidth}
            height={renderedHeight}
            on:click={handleClick}
            on:mousedown={handleMouseDown}
            on:mousemove={handleMouseMove}
            on:mouseup={handleMouseUp}
            class="border border-gray-300 rounded shadow absolute inset-0"
            style="cursor: crosshair; width: 100%; height: 100%; background: transparent; z-index:2;"
        ></canvas>
    </div>
</div>
