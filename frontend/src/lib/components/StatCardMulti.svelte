<script lang="ts">
    type StatItem = {
        label: string;
        value: number;
        color?: string;
    };

    type StatCardMultiProps = {
        title: string;
        totalValue: number;
        items: StatItem[];
        icon: any;  // Lucide icon component
        iconColor?: string;
        onclick?: () => void;
    };

    let { title, totalValue, items, icon: Icon, iconColor = 'text-blue-600', onclick }: StatCardMultiProps = $props();

    function formatNumber(num: number): string {
        return num.toLocaleString();
    }

    function handleClick() {
        if (onclick) {
            onclick();
        }
    }

    function handleKeyDown(e: KeyboardEvent) {
        if (e.key === 'Enter' && onclick) {
            onclick();
        }
    }
</script>

{#if onclick}
<button
    class="bg-white rounded-2xl shadow p-3 xl:p-6 flex items-start justify-between h-full transition-shadow cursor-pointer hover:shadow-xl w-full text-left"
    onclick={handleClick}
>
    <div class="flex-1 flex flex-col justify-center">
        <p class="text-xs xl:text-sm font-medium text-gray-500 mb-0.5 xl:mb-1">{title}</p>
        <p class="text-xl xl:text-3xl font-bold text-gray-800">{formatNumber(totalValue)}</p>
        {#if items.length > 0}
            <p class="text-xs text-gray-400 mt-1">Click to view breakdown</p>
        {/if}
    </div>
    <div class="p-2 xl:p-3 rounded-full bg-gray-50 {iconColor} flex-shrink-0">
        <Icon class="h-4 w-4 xl:h-6 xl:w-6" />
    </div>
</button>
{:else}
<div class="bg-white rounded-2xl shadow p-3 xl:p-6 flex items-start justify-between h-full transition-shadow hover:shadow-lg">
    <div class="flex-1 flex flex-col justify-center">
        <p class="text-xs xl:text-sm font-medium text-gray-500 mb-0.5 xl:mb-1">{title}</p>
        <p class="text-xl xl:text-3xl font-bold text-gray-800">{formatNumber(totalValue)}</p>
    </div>
    <div class="p-2 xl:p-3 rounded-full bg-gray-50 {iconColor} flex-shrink-0">
        <Icon class="h-4 w-4 xl:h-6 xl:w-6" />
    </div>
</div>
{/if}
