<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Chart, Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale, LineController, Filler } from 'chart.js';

  Chart.register(
    Title, Tooltip, Legend,
    LineElement, PointElement,
    CategoryScale, LinearScale, LineController,
    Filler
  );

  type LineChartProps = {
    data?: {
      labels: string[];
      datasets: {
        label: string;
        data: number[];
        borderColor: string;
        backgroundColor: string;
        fill: boolean;
        tension: number;
      }[];
    };
    animate?: boolean;
    options?: any;
  };

  let {
    data = {
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
    },
    animate = false,
    options = {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 750,
        easing: 'easeInOutQuart'
      },
      plugins: {
        legend: { position: "top" as const },
      },
      scales: {
        x: {
          beginAtZero: true
        },
        y: {
          beginAtZero: true
        }
      }
    }
  }: LineChartProps = $props();

  let canvasElement = $state<HTMLCanvasElement | undefined>(undefined);
  let chart: Chart | null = null;

  onMount(() => {
    if (!canvasElement) return;

    chart = new Chart(canvasElement, {
      type: 'line',
      data: $state.snapshot(data),
      options
    });
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
      chart = null;
    }
  });

  // Update chart when data or options change
  $effect(() => {
    if (chart) {
      chart.data = $state.snapshot(data);
      chart.options = options;
      // Use animation based on the animate prop
      chart.update(animate ? 'active' : 'none');
    }
  });
</script>

<div class="w-full h-full">
  <canvas bind:this={canvasElement}></canvas>
</div>

<style>
/* You can use Tailwind instead of writing CSS here, e.g. give classes to the div */
</style>
