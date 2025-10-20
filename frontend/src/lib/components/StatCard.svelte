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

<div class="bg-white rounded-2xl shadow p-6 flex items-start justify-between min-h-[150px] hover:shadow-lg transition-shadow">
    <div class="flex-1">
        <p class="text-sm font-medium text-gray-500 mb-1">{title}</p>
        <p class="text-3xl font-bold text-gray-800">{formatNumber(value)}</p>
    </div>
    <div class="p-3 rounded-full bg-gray-50 {iconColor}">
        <Icon class="h-6 w-6" />
    </div>
</div>
