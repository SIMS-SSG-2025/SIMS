<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Chart, Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale, LineController } from 'chart.js';

  Chart.register(
    Title, Tooltip, Legend,
    LineElement, PointElement,
    CategoryScale, LinearScale, LineController
  );

  export let data = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    datasets: [
      {
        label: "Placeholder Data",
        data: [12, 19, 3, 5, 2, 3],
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.5)",
        fill: true,
        tension: 0.4
      }
    ]
  };

  export let options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" as const },
      title: { display: true, text: "Line Chart (Placeholder)" }
    },
    scales: {
      x: {
        beginAtZero: true
      },
      y: {
        beginAtZero: true
      }
    }
  };

  let canvasElement: HTMLCanvasElement;
  let chart: Chart | null = null;

  onMount(() => {
    if (!canvasElement) return;

    chart = new Chart(canvasElement, {
      type: 'line',
      data,
      options
    });
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
      chart = null;
    }
  });

  // Optionally, if data or options can change, you can use $: reactive blocks:

  $: if (chart) {
    chart.data = data;
    chart.options = options;
    chart.update();
  }
</script>

<div class="h-64 w-full">
  <canvas bind:this={canvasElement} class="w-full h-full"></canvas>
</div>

<style>
/* You can use Tailwind instead of writing CSS here, e.g. give classes to the div */
</style>
