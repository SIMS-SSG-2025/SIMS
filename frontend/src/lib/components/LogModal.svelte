<script lang="ts">
    import Modal from "./modal.svelte";
    import { onMount, onDestroy } from "svelte";
    import { CircleX, TriangleAlert, Info as InfoIcon, CircleCheckBig, FileText } from 'lucide-svelte';
    import { API_BASE_URL } from "$lib/api/config";

    let {
        open = $bindable(false),
        onClose = () => {}
    }: {
        open: boolean;
        onClose: () => void;
    } = $props();

    let logs = $state<string[]>([]);
    let loading = $state(false);
    let error = $state<string | null>(null);
    let logInterval: any;

    // Filter state
    let filters = $state({
        ERROR: true,
        WARNING: true,
        INFO: true,
        DETECTION: true
    });

    // Computed filtered logs
    let filteredLogs = $derived(logs.filter(log => {
        const parsedLog = formatLogMessage(log);

        //  detection log
        if (parsedLog.isDetection) {
            return filters.DETECTION;
        }

        // Regular log level filtering for ERROR, WARNING, INFO
        return filters[parsedLog.level as keyof typeof filters] !== false;
    }));

    async function fetchLogs() {
        try {
            loading = true;
            error = null;

            const response = await fetch(`${API_BASE_URL}/logs`);

            if (!response.ok) {
                throw new Error(`Failed to fetch logs: ${response.statusText}`);
            }

            const data = await response.json();

            logs = data.logs || [];
        } catch (err) {
            console.error('Error fetching logs:', err);
            error = err instanceof Error ? err.message : 'Failed to fetch logs';
            // Keep existing logs on error instead of clearing them
        } finally {
            loading = false;
        }
    }

    function getLogLevelStyle(log: string): string {
        const logUpper = log.toUpperCase();
        // Check for DETECTION first to override INFO styling
        if (logUpper.includes('- DETECTION -')) {
            return 'text-purple-700 bg-purple-50 border-purple-200';
        } else if (logUpper.includes('ERROR')) {
            return 'text-red-700 bg-red-50 border-red-200';
        } else if (logUpper.includes('WARNING') || logUpper.includes('WARN')) {
            return 'text-yellow-700 bg-yellow-50 border-yellow-200';
        } else if (logUpper.includes('INFO')) {
            return 'text-blue-700 bg-blue-50 border-blue-200';
        }

        // Default styling for unknown log levels
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }

    function formatLogMessage(log: string): { level: string; message: string; timestamp: string; isDetection: boolean } {
        // Updated pattern to match your log format: "2025-10-09 11:32:45 - DatabaseManager - INFO - Location inserted: ID=1, Name=Makerspace"
        const patterns = [
            /(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*([^-]+)\s*-\s*(ERROR|WARNING|INFO)\s*-\s*(.*)/i,
            /(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]?\d*)\s*[-\s]*\s*(ERROR|WARNING|INFO)\s*[-\s]*\s*(.*)/i,
            /(ERROR|WARNING|INFO):\s*(.*)/i,
            /\[(ERROR|WARNING|INFO)\]\s*(.*)/i
        ];
        for (const pattern of patterns) {
            const match = log.match(pattern);
            if (match) {
                if (match.length === 5) {
                    // Format: timestamp - component - level - message
                    const component = match[2].trim();
                    const isDetection = component.toUpperCase() === 'DETECTION';
                    return {
                        timestamp: match[1],
                        level: match[3].toUpperCase(),
                        message: `${match[2]} - ${match[4]}`,
                        isDetection
                    };
                } else if (match.length === 4) {
                    return {
                        timestamp: match[1],
                        level: match[2].toUpperCase(),
                        message: match[3],
                        isDetection: false
                    };
                } else if (match.length === 3) {
                    return {
                        timestamp: '',
                        level: match[1].toUpperCase(),
                        message: match[2],
                        isDetection: false
                    };
                }
            }
        }

        // If no pattern matches, return the original log as message
        return {
            timestamp: '',
            level: 'INFO',
            message: log,
            isDetection: log.toUpperCase().includes('DETECTION')
        };
    }

    onMount(() => {
        fetchLogs(); // Initial fetch
        logInterval = setInterval(fetchLogs, 5000); // Fetch every 5 seconds
    });

    onDestroy(() => {
        if (logInterval) {
            clearInterval(logInterval);
        }
    });
</script>

<Modal {open} {onClose} modalClass="p-6 w-full max-w-4xl max-h-[90vh] overflow-auto">
    <div class="w-full">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">System Logs</h2>

        <!-- Filter Controls -->
        <div class="mb-4 p-4 bg-white border border-gray-200 rounded-lg">
            <h3 class="text-sm font-medium text-gray-700 mb-3">Filter by Log Level:</h3>
            <div class="flex flex-wrap gap-4">
                <label class="flex items-center space-x-2 cursor-pointer">
                    <input
                        type="checkbox"
                        bind:checked={filters.ERROR}
                        class="rounded border-gray-300 text-red-600 focus:ring-red-500"
                    />
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-red-100 text-red-800">
                        <CircleX class="w-3 h-3 mr-1" />
                        ERROR
                    </span>
                </label>

                <label class="flex items-center space-x-2 cursor-pointer">
                    <input
                        type="checkbox"
                        bind:checked={filters.WARNING}
                        class="rounded border-gray-300 text-yellow-600 focus:ring-yellow-500"
                    />
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-yellow-100 text-yellow-800">
                        <TriangleAlert class="w-3 h-3 mr-1" />
                        WARNING
                    </span>
                </label>

                <label class="flex items-center space-x-2 cursor-pointer">
                    <input
                        type="checkbox"
                        bind:checked={filters.INFO}
                        class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-800">
                        <InfoIcon class="w-3 h-3 mr-1" />
                        INFO
                    </span>
                </label>

                <label class="flex items-center space-x-2 cursor-pointer">
                    <input
                        type="checkbox"
                        bind:checked={filters.DETECTION}
                        class="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                    />
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-purple-100 text-purple-800">
                        <CircleCheckBig class="w-3 h-3 mr-1" />
                        DETECTION
                    </span>
                </label>
            </div>

            <!-- Quick filter buttons -->
            <div class="flex gap-2 mt-3 pt-3 border-t border-gray-200">
                <button
                    class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition"
                    onclick={() => {
                        filters.ERROR = true;
                        filters.WARNING = true;
                        filters.INFO = true;
                        filters.DETECTION = true;
                    }}
                >
                    Select All
                </button>
                <button
                    class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition"
                    onclick={() => {
                        filters.ERROR = false;
                        filters.WARNING = false;
                        filters.INFO = false;
                        filters.DETECTION = false;
                    }}
                >
                    Clear All
                </button>
                <button
                    class="px-3 py-1 text-xs bg-purple-100 hover:bg-purple-200 text-purple-700 rounded transition"
                    onclick={() => {
                        filters.ERROR = false;
                        filters.WARNING = false;
                        filters.INFO = false;
                        filters.DETECTION = true;
                    }}
                >
                    Detections Only
                </button>
            </div>
        </div>

        {#if error}
            <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                <p class="font-medium">Error loading logs:</p>
                <p class="text-sm">{error}</p>
            </div>
        {/if}
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-96 overflow-y-auto">
            {#if filteredLogs.length > 0}
                <div class="space-y-2 text-sm">
                    {#each filteredLogs as log}
                        {@const parsedLog = formatLogMessage(log)}
                        {@const styleClass = getLogLevelStyle(log)}
                        <div class="border rounded-lg p-3 {styleClass}">
                            <div class="flex items-start gap-3">
                                {#if parsedLog.level}
                                    <span class="inline-flex items-center justify-center px-2 py-1 rounded-md text-xs font-semibold uppercase tracking-wide w-20
                                        {parsedLog.level === 'ERROR' ? 'bg-red-100 text-red-800' : ''}
                                        {parsedLog.level === 'WARNING' || parsedLog.level === 'WARN' ? 'bg-yellow-100 text-yellow-800' : ''}
                                        {parsedLog.level === 'INFO' && !parsedLog.isDetection ? 'bg-blue-100 text-blue-800' : ''}
                                        {parsedLog.isDetection ? 'bg-purple-100 text-purple-800' : ''}
                                    ">
                                        {parsedLog.isDetection ? 'DETECT' : parsedLog.level}
                                    </span>
                                {/if}
                                <div class="flex-1 min-w-0">
                                    {#if parsedLog.timestamp}
                                        <div class="text-xs opacity-70 mb-1 font-mono">{parsedLog.timestamp}</div>
                                    {/if}
                                    <div class="font-mono whitespace-pre-line break-words">{parsedLog.message}</div>
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            {:else}
                <div class="text-center text-gray-500 py-8">
                    <FileText class="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    {#if logs.length > 0}
                        <p>No logs match the current filters.</p>
                        <p class="text-sm mt-2">Try adjusting your filter settings above.</p>
                    {:else}
                        <p>No log messages yet.</p>
                    {/if}
                </div>
            {/if}
        </div>
    </div>
</Modal>
