<script lang="ts">
    import Modal from "./modal.svelte";
    import { onMount, onDestroy } from "svelte";

    export let open: boolean = false;
    export let onClose: () => void = () => {};

    let logs: string[] = [];
    let loading = false;
    let error: string | null = null;
    let logInterval: any;

    // Filter state
    let filters = {
        ERROR: true,
        WARNING: true,
        INFO: true,
        DETECTION: true
    };

    // Computed filtered logs
    $: filteredLogs = logs.filter(log => {
        const parsedLog = formatLogMessage(log);

        // Check if it's a detection log using the new isDetection property
        if (parsedLog.isDetection) {
            return filters.DETECTION;
        }

        // Regular log level filtering for ERROR, WARNING, INFO
        return filters[parsedLog.level as keyof typeof filters] !== false;
    });

    const mockLogs = [
        "2025-10-09 11:32:45 - DatabaseManager - INFO - Location inserted: ID=1, Name=Makerspace",
        "2025-10-09 11:32:50 - DeviceRuntime - WARNING - No response received for status check",
        "2025-10-09 11:32:55 - DatabaseManager - INFO - Connection established successfully",
        "2025-10-09 11:33:00 - DeviceRuntime - ERROR - Failed to initialize camera module",
        "2025-10-09 11:33:05 - DETECTION - INFO - Person without helmet detected in Zone A",
        "2025-10-09 11:33:10 - DeviceRuntime - WARNING - High CPU usage detected: 89%",
        "2025-10-09 11:33:15 - InferenceEngine - INFO - PPE detection model loaded successfully",
        "2025-10-09 11:33:20 - DeviceRuntime - ERROR - Network connection timeout",
        "2025-10-09 11:33:25 - DETECTION - INFO - Safety vest missing for worker ID 123",
        "2025-10-09 11:33:30 - InferenceEngine - INFO - Processing frame 12345",
        "2025-10-09 11:33:35 - DeviceRuntime - ERROR - Authentication failed for device registration",
        "2025-10-09 11:33:40 - DETECTION - INFO - Unauthorized person in restricted area",
        "2025-10-09 11:33:45 - DatabaseManager - INFO - Zone configuration updated successfully"
    ];

    function loadMockLogs() {
        loading = true;
        setTimeout(() => {
            logs = [...mockLogs];
            loading = false;
        }, 500); // Simulate network delay
    }

    async function fetchLogs() {
        try {
            // IP jetson: 10.10.67.44
            const response = await fetch("http://10.10.67.44:8000/logs");
            if (!response.ok) {
                throw new Error(`Error fetching logs: ${response.statusText}`);
            }
            const data = await response.json();
            console.log(data);
            logs = data.logs || [];
        } catch (err: any) {
            error = err.message;
        } finally {
            loading = false;
        }
       //loadMockLogs();
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
        logInterval = setInterval(fetchLogs, 5000);
        fetchLogs(); // Initial fetch
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
                        <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                        </svg>
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
                        <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                        </svg>
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
                        <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                        </svg>
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
                        <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" clip-rule="evenodd"/>
                        </svg>
                        DETECTION
                    </span>
                </label>
            </div>

            <!-- Quick filter buttons -->
            <div class="flex gap-2 mt-3 pt-3 border-t border-gray-200">
                <button
                    class="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition"
                    on:click={() => {
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
                    on:click={() => {
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
                    on:click={() => {
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
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
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
