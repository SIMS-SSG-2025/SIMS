<script lang="ts">
    import { onMount } from 'svelte';
    import type { ObjectPosition } from '$lib/api/config';

    // Props
    let {
        positions = [],
        width = 1920,
        height = 1080,
        lineWidth = 2,
        opacity = 0.7,
        showPoints = true
    }: {
        positions?: ObjectPosition[];
        width?: number;
        height?: number;
        lineWidth?: number;
        opacity?: number;
        showPoints?: boolean;
    } = $props();

    let canvas = $state<HTMLCanvasElement>();
    let ctx = $state<CanvasRenderingContext2D>();

    // Generate distinct colors for different objects
    const objectColors: Map<number, string> = new Map();
    const colorPalette = [
        'rgba(231, 106, 35, ',   // Orange (SIMS primary)
        'rgba(59, 130, 246, ',    // Blue
        'rgba(34, 197, 94, ',     // Green
        'rgba(168, 85, 247, ',    // Purple
        'rgba(236, 72, 153, ',    // Pink
        'rgba(251, 191, 36, ',    // Yellow
        'rgba(239, 68, 68, ',     // Red
        'rgba(20, 184, 166, ',    // Teal
        'rgba(249, 115, 22, ',    // Deep Orange
        'rgba(139, 92, 246, ',    // Violet
    ];

    onMount(() => {
        if (canvas) {
            ctx = canvas.getContext('2d') ?? undefined;
        }
    });

    // Effect to redraw when positions change
    $effect(() => {
        if (positions.length > 0 && ctx && canvas) {
            drawMovementTrails();
        }
    });

    function drawMovementTrails() {
        if (!ctx || !canvas) return;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Group positions by object_id and sort by time
        const objectPaths = new Map<number, ObjectPosition[]>();

        positions.forEach(pos => {
            if (!objectPaths.has(pos.object_id)) {
                objectPaths.set(pos.object_id, []);
            }
            objectPaths.get(pos.object_id)!.push(pos);
        });

        // Sort each object's positions by time
        objectPaths.forEach((path, objectId) => {
            path.sort((a, b) => {
                const timeA = new Date(a.time).getTime();
                const timeB = new Date(b.time).getTime();
                return timeA - timeB;
            });
        });

        console.log('Movement trails:', {
            totalPositions: positions.length,
            uniqueObjects: objectPaths.size,
            objectPaths: Array.from(objectPaths.entries()).map(([id, path]) => ({
                objectId: id,
                points: path.length
            }))
        });

        // Assign colors to objects
        let colorIndex = 0;
        objectPaths.forEach((path, objectId) => {
            if (!objectColors.has(objectId)) {
                objectColors.set(objectId, colorPalette[colorIndex % colorPalette.length]);
                colorIndex++;
            }
        });

        // Draw each object's path
        objectPaths.forEach((path, objectId) => {
            if (path.length < 2) return; // Need at least 2 points for a line

            const baseColor = objectColors.get(objectId)!;

            // Draw the path as a continuous line
            ctx!.beginPath();

            // Start at first position
            const startX = path[0].x * canvas!.width;
            const startY = path[0].y * canvas!.height;
            ctx!.moveTo(startX, startY);

            // Draw lines to subsequent positions
            for (let i = 1; i < path.length; i++) {
                const x = path[i].x * canvas!.width;
                const y = path[i].y * canvas!.height;
                ctx!.lineTo(x, y);
            }

            // Style and stroke the path
            ctx!.strokeStyle = baseColor + opacity + ')';
            ctx!.lineWidth = lineWidth;
            ctx!.lineCap = 'round';
            ctx!.lineJoin = 'round';
            ctx!.stroke();

            // Draw points if enabled
            if (showPoints) {
                path.forEach((pos, index) => {
                    const x = pos.x * canvas!.width;
                    const y = pos.y * canvas!.height;

                    ctx!.beginPath();
                    ctx!.arc(x, y, lineWidth * 1.5, 0, Math.PI * 2);

                    // First point larger and more opaque
                    if (index === 0) {
                        //ctx!.fillStyle = baseColor + Math.min(1, opacity * 1.3) + ')';
                        //ctx!.arc(x, y, lineWidth * 2.5, 0, Math.PI * 2);
                    } else if (index === path.length - 1) {
                        // Last point slightly larger
                        //ctx!.fillStyle = baseColor + opacity + ')';
                        //ctx!.arc(x, y, lineWidth * 2, 0, Math.PI * 2);
                    } else {
                        //ctx!.fillStyle = baseColor + (opacity * 0.6) + ')';
                    }

                    //ctx!.fill();
                });
            }
        });
    }

    // Public method to clear the trails
    export function clear() {
        if (ctx && canvas) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        objectColors.clear();
    }

    // Public method to redraw
    export function redraw() {
        drawMovementTrails();
    }
</script>

<canvas
    bind:this={canvas}
    width={width}
    height={height}
    class="absolute inset-0 w-full h-full"
    style="pointer-events: none; z-index: 3;"
></canvas>

<style>
    canvas {
        image-rendering: optimizeQuality;
    }
</style>
