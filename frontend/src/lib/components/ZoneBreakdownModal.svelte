<script lang="ts">
    import Modal from './modal.svelte';
    import { Ban } from 'lucide-svelte';

    type ZoneBreakdownItem = {
        label: string;
        value: number;
        color?: string;
    };

    type ZoneBreakdownModalProps = {
        open: boolean;
        items: ZoneBreakdownItem[];
        totalEntries: number;
        onClose: () => void;
    };

    let { open, items, totalEntries, onClose }: ZoneBreakdownModalProps = $props();

    function formatNumber(num: number): string {
        return num.toLocaleString();
    }

    function calculatePercentage(value: number): string {
        if (totalEntries === 0) return '0';
        return ((value / totalEntries) * 100).toFixed(1);
    }
</script>

<Modal {open} {onClose} modalClass="p-6 w-full max-w-md">
    <div class="w-full">
        <div class="flex items-center gap-3 mb-6">
            <div class="p-3 rounded-full bg-red-50 text-red-600">
                <Ban class="h-6 w-6" />
            </div>
            <div>
                <h2 class="text-xl font-semibold text-gray-800">Risk Zone Violations</h2>
                <p class="text-sm text-gray-500">Total: {formatNumber(totalEntries)} Violations</p>
            </div>
        </div>

        {#if items.length > 0}
            <div class="space-y-4">
                {#each items as item}
                    <div class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center gap-2 flex-1 min-w-0">
                                <span class="w-3 h-3 rounded-full flex-shrink-0 {item.color || 'bg-gray-400'}"></span>
                                <span class="font-medium text-gray-800 truncate">{item.label}</span>
                            </div>
                            <span class="text-2xl font-bold text-gray-800 ml-4">{formatNumber(item.value)}</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div
                                class="{item.color?.replace('bg-', 'bg-') || 'bg-gray-400'} h-2 rounded-full transition-all duration-500"
                                style="width: {calculatePercentage(item.value)}%"
                            ></div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1 text-right">{calculatePercentage(item.value)}% of total</p>
                    </div>
                {/each}
            </div>
        {:else}
            <div class="text-center py-8 text-gray-400">
                <Ban class="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No zone violations</p>
            </div>
        {/if}
    </div>
</Modal>
