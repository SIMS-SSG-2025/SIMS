<script lang="ts">
    import Modal from './modal.svelte';

    type DateRangePickerProps = {
        open: boolean;
        onClose: () => void;
        onApply: (start: Date, end: Date) => void;
    };

    let { open, onClose, onApply }: DateRangePickerProps = $props();

    let startDate = $state('');
    let endDate = $state('');
    let error = $state('');

    function formatDateForInput(date: Date): string {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    // Initialize with default values when modal opens
    $effect(() => {
        if (open) {
            const today = new Date();
            const weekAgo = new Date();
            weekAgo.setDate(today.getDate() - 7);

            startDate = formatDateForInput(weekAgo);
            endDate = formatDateForInput(today);
            error = '';
        }
    });

    function handleApply() {
        error = '';

        if (!startDate || !endDate) {
            error = 'Please select both start and end dates';
            return;
        }

        const start = new Date(startDate);
        const end = new Date(endDate);

        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
            error = 'Invalid date format';
            return;
        }

        if (start > end) {
            error = 'Start date must be before end date';
            return;
        }

        if (end > new Date()) {
            error = 'End date cannot be in the future';
            return;
        }

        onApply(start, end);
        onClose();
    }

    function handleQuickSelect(days: number) {
        const end = new Date();
        const start = new Date();
        start.setDate(end.getDate() - days);

        startDate = formatDateForInput(start);
        endDate = formatDateForInput(end);
    }
</script>

<Modal {open} {onClose} modalClass="p-6 w-full max-w-md">
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <h2 class="text-2xl font-semibold text-gray-800">Custom Date Range</h2>
        </div>

        <!-- Quick select buttons -->
        <div class="space-y-2">
            <p class="text-sm font-medium text-gray-700">Quick Select</p>
            <div class="flex gap-2 flex-wrap">
                <button
                    onclick={() => handleQuickSelect(7)}
                    class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                    Last 7 days
                </button>
                <button
                    onclick={() => handleQuickSelect(14)}
                    class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                    Last 14 days
                </button>
                <button
                    onclick={() => handleQuickSelect(30)}
                    class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                    Last 30 days
                </button>
                <button
                    onclick={() => handleQuickSelect(90)}
                    class="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                    Last 90 days
                </button>
            </div>
        </div>

        <!-- Date inputs -->
        <div class="space-y-4">
            <div>
                <label for="start-date" class="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                </label>
                <input
                    id="start-date"
                    type="date"
                    bind:value={startDate}
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#E76A23] focus:border-transparent"
                    max={formatDateForInput(new Date())}
                />
            </div>

            <div>
                <label for="end-date" class="block text-sm font-medium text-gray-700 mb-2">
                    End Date
                </label>
                <input
                    id="end-date"
                    type="date"
                    bind:value={endDate}
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#E76A23] focus:border-transparent"
                    max={formatDateForInput(new Date())}
                />
            </div>
        </div>

        {#if error}
            <div class="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p class="text-sm text-red-600">{error}</p>
            </div>
        {/if}

        <!-- Action buttons -->
        <div class="flex gap-3">
            <button
                onclick={handleApply}
                class="flex-1 px-4 py-2.5 bg-[#E76A23] text-white rounded-lg hover:bg-[#d15e1e] transition font-medium"
            >
                Apply
            </button>
            <button
                onclick={onClose}
                class="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition font-medium"
            >
                Cancel
            </button>
        </div>
    </div>
</Modal>
