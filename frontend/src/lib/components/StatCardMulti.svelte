<script lang="ts">
    type StatItem = {
        label: string;
        value: number;
        color?: string;
        icon?: string;
    };

    type StatCardMultiProps = {
        title: string;
        items: StatItem[];
        icon: string;
        iconColor?: string;
    };

    let { title, items, icon, iconColor = 'text-blue-600' }: StatCardMultiProps = $props();

    function formatNumber(num: number): string {
        return num.toLocaleString();
    }
</script>

<div class="bg-white rounded-2xl shadow p-6 hover:shadow-lg transition-shadow min-h-[150px] flex flex-col">
    <!-- Header with title and icon -->
    <div class="flex items-center justify-between mb-4">
        <p class="text-sm font-medium text-gray-500">{title}</p>
        <div class="p-3 rounded-full bg-gray-50 {iconColor}">
            {@html icon}
        </div>
    </div>

    <!-- Mini cards row -->
    <div class="flex gap-3 flex-1">
        {#each items as item}
            <div class="flex-1 bg-gradient-to-br from-orange-50 to-white rounded-xl p-3 border border-orange-100 hover:border-orange-300 transition-all">
                <div class="flex items-center gap-2 mb-1">
                    {#if item.icon}
                        <div class="{item.color || 'text-orange-600'}">
                            {@html item.icon}
                        </div>
                    {/if}
                    <p class="text-xs font-medium text-gray-600">{item.label}</p>
                </div>
                <p class="text-3xl font-bold {item.color || 'text-gray-800'} mt-1">
                    {formatNumber(item.value)}
                </p>
            </div>
        {/each}
    </div>
</div>
