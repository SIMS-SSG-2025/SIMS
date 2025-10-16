<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { Chart, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, BarController } from 'chart.js';

    Chart.register(
        Title, Tooltip, Legend,
        BarElement,
        CategoryScale, LinearScale, BarController
    );

    type BarChartProps = {
        labels: string[];
        datasets: {
            label: string;
            data: number[];
            backgroundColor: string;
            borderColor?: string;
            borderWidth?: number;
        }[];
        title?: string;
    };

    let { labels, datasets, title = "" }: BarChartProps = $props();

    let canvasElement: HTMLCanvasElement;
    let chart: Chart | null = null;

    onMount(() => {
        if (!canvasElement) return;

        chart = new Chart(canvasElement, {
            type: 'bar',
            data: {
                labels: $state.snapshot(labels),
                datasets: $state.snapshot(datasets)
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "top" as const,
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    title: {
                        display: !!title,
                        text: title,
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                }
            }
        });
    });

    onDestroy(() => {
        if (chart) {
            chart.destroy();
        }
    });

    // Update chart when data changes
    $effect(() => {
        if (chart) {
            chart.data.labels = $state.snapshot(labels);
            chart.data.datasets = $state.snapshot(datasets);
            chart.update();
        }
    });
</script>

<div class="w-full h-full min-h-[300px]">
    <canvas bind:this={canvasElement}></canvas>
</div>
