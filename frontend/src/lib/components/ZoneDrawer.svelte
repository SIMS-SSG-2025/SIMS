<script lang="ts">
    export let onFinishZone: (points: { x: number; y: number }[], name: string) => void;
    import { onMount } from "svelte";

    interface Point {
        x: number;
        y: number;
    }
    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D;
    let img: HTMLImageElement;
    let drawing: boolean = false;
    let points: Point[] = [];
    let draggingPointsIndex: number | null = null;

    onMount(() => {
        ctx = canvas.getContext("2d")!;
        img = new Image();
        img.src = "/snapshot.jpg";
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
        };
    })

    function getMousePos(event: MouseEvent): Point {
        const rect = canvas.getBoundingClientRect();
        return {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
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
        redraw();
    }

    function handleFinish(): void {
        if(points.length > 2) {
            // Here you would typically send the points to the backend
            const normalizedPoints = points.map(p => ({
                x: p.x / canvas.width,
                y: p.y / canvas.height
            }));
            console.log("Zone JSON:", JSON.stringify({ points: normalizedPoints }));
            onFinishZone(normalizedPoints, "Zone A");
            points = [];
            redraw();
        }
        else {
            alert("A zone must have at least 3 points.");
        }

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
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);

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
    }

</script>

<div>
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
    <canvas
        bind:this={canvas}
        on:click={handleClick}
        on:mousedown={handleMouseDown}
        on:mousemove={handleMouseMove}
        on:mouseup={handleMouseUp}
        class="border border-gray-300 rounded shadow"
        style="cursor: crosshair;"
    ></canvas>
</div>
