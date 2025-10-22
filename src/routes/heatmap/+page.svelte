<script>
    import {onMount} from "svelte";
    import h337 from "heatmap.js";

    let coords = [];
    let snapshot = "/snapshot.png";

    onMount(async () => {
        const res = await fetch("http://127.0.0.1:8000/heatmap_coords");
        coords = await res.json();

        const heatmapInstance = h337.create({
            container: document.getElementById("heatmap-container"),
            radius: 30, maxOpacity: 0.6, minOpacity: 0, blur: 0.5
        });

        const data = coords.map(c=>({x: c.x, y: c.y, value: 1}));
        heatmapInstance.heatmap.setData({ max: 10, data});
    });


</script>


<style>
    #heatmap-container {
        position: relative;
    }
</style>

<div
        id="heatmap-container"
        style="background-image: url({snapshot}); width: 800px; height: 600px;"
></div>