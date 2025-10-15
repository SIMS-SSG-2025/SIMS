<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { Chart, Title, Tooltip, Legend, ArcElement, DoughnutController } from 'chart.js';

    Chart.register(
        Title, Tooltip, Legend,
        ArcElement,
        DoughnutController
    );

    type PieChartProps = {
        labels: string[];
        data: number[];
        backgroundColor: string[];
        title?: string;
        isDoughnut?: boolean;
    };

    let { labels, data, backgroundColor, title = "Pie Chart", isDoughnut = true }: PieChartProps = $props();

    let canvasElement: HTMLCanvasElement;
    let chart: Chart | null = null;

    onMount(() => {
        if (!canvasElement) return;

        chart = new Chart(canvasElement, {
            type: isDoughnut ? 'doughnut' : 'pie',
            data: {
                labels: $state.snapshot(labels),
                datasets: [{
                    data: $state.snapshot(data),
                    backgroundColor: $state.snapshot(backgroundColor),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom" as const,
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12
                            }
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
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
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
            chart.data.datasets[0].data = $state.snapshot(data);
            chart.data.datasets[0].backgroundColor = $state.snapshot(backgroundColor);
            chart.update();
        }
    });
</script>

<div class="w-full h-full min-h-[300px]">
    <canvas bind:this={canvasElement}></canvas>
</div>
