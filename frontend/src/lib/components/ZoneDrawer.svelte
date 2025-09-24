<script>
    import { onMount } from "svelte";
    let canvas;
    let ctx;
    let img;
    let drawing = false;
    let points = [];

    onMount(() => {
        ctx = canvas.getContext("2d");
        img = new Image();
        img.src = "/snapshot.jpg";
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
        };
    })

    function handleClick(event) {
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        points.push([x, y]);
        console.log(points);
        redraw();
    }

    function handleUndo() {
        points.pop();
        console.log(points);
        redraw();
    }

    function handleFinish() {
        if(points.length > 2) {
            // Here you would typically send the points to the backend
            console.log("Zone JSON:", JSON.stringify({ points }));
            points = [];
            redraw();
        }
        else {
            alert("A zone must have at least 3 points.");
        }

    }

    function redraw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);

        if (points.length > 0) {
        // Draw filled polygon if 3+ points
        if (points.length >= 3) {
            ctx.beginPath();
            ctx.moveTo(points[0][0], points[0][1]);
            for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i][0], points[i][1]);
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
            if (Array.isArray(pt) && pt.length === 2) {
            const [px, py] = pt;
            ctx.beginPath();
            ctx.arc(px, py, 4, 0, Math.PI * 2);
            ctx.fillStyle = "blue";
            ctx.fill();
            }
        });
        }
    }
</script>

<div class="controls">
    <button on:click={handleUndo}>Undo</button>
    <button on:click={handleFinish}>Finish Zone</button>
</div>

<canvas bind:this={canvas} on:click={handleClick} style="border:1px solid #ccc; cursor: crosshair;" />
