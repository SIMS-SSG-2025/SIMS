<script>
    import { onMount,tick } from 'svelte';
    let heatmapContainer;
    let heatmap;
    let imageurl = "http://127.0.0.1:8000/snapshot.png";
    async function loadHeatmap() {
        const response_coords = await fetch("http://127.0.0.1:8000/heatmap_coords");
        const data = await response_coords.json();
        let dataMax = Math.max(...data.data.map(p=>p.value));
        let maxVal = Math.max(dataMax,5);
        if (heatmap) {
            heatmap.setData({
                max: maxVal, data:data.data
            });
        }
    }



    onMount(()=>{
        heatmap = window.h337.create({ container: heatmapContainer, radius: 20, });

        loadHeatmap();
        setInterval(()=>{
            imageurl = `http://127.0.0.1:8000/snapshot.png?time=${Date.now()}`;
            loadHeatmap();
        },1000);
    });

</script>

<div
        id="heatmapContainer"
        bind:this={heatmapContainer}
        style="width: 500px; height: 400px; border: 2px solid #ff0000; margin: 2rem auto;">

    <img src={imageurl} alt="Snapshot" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0;"/>
</div>