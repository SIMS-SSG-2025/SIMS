<script lang="ts">
    import type { Snippet } from 'svelte';

    type StatCardProps = {
        title: string;
        value: number;
        icon: any;  // Lucide icon component
        iconColor?: string;
    };

    let { title, value, icon: Icon, iconColor = 'text-blue-600' }: StatCardProps = $props();

    function formatNumber(num: number): string {
        return num.toLocaleString();
    }
</script>

<div class="bg-white rounded-2xl shadow p-3 xl:p-6 flex items-start justify-between h-full hover:shadow-lg transition-shadow">
    <div class="flex-1 flex flex-col justify-center">
        <p class="text-xs xl:text-sm font-medium text-gray-500 mb-0.5 xl:mb-1">{title}</p>
        <p class="text-xl xl:text-3xl font-bold text-gray-800">{formatNumber(value)}</p>
    </div>
    <div class="p-2 xl:p-3 rounded-full bg-gray-50 {iconColor} flex-shrink-0">
        <Icon class="h-4 w-4 xl:h-6 xl:w-6" />
    </div>
</div>
