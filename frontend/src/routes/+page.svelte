<script lang="ts">
    import BarChart from "$lib/components/BarChart.svelte";
    import LineChart from "$lib/components/LineChart.svelte";
    import PieChart from "$lib/components/PieChart.svelte";
    import Modal from "$lib/components/modal.svelte";
    import ConfigSetupModal from "$lib/components/ConfigSetupModal.svelte";
    import LogModal from "$lib/components/LogModal.svelte";
    import ChartModal from "$lib/components/ChartModal.svelte";
    import ZoneBreakdownModal from "$lib/components/ZoneBreakdownModal.svelte";
    import StatCard from "$lib/components/StatCard.svelte";
    import StatCardMulti from "$lib/components/StatCardMulti.svelte";
    import DateRangePicker from "$lib/components/DateRangePicker.svelte";
    import ZoneDrawer from "$lib/components/ZoneDrawer.svelte";
    import { onMount } from "svelte";
    import { fetchCurrentConfig, getSystemStatus, type Config } from "$lib/api/config";
    import {
        type DashboardStats,
        type TimeRangeOption,
        type TimeRange,
        type DetectionBarChartData,
        type PPEComplianceData,
        type Event,
        calculateTimeRange,
        fetchEventsForLocation,
        calculateStatsFromEvents,
        calculatePPEComplianceFromEvents,
        createChartDataFromEvents,
        findEarliestEventTime,
        fetchDetectionBarChartData,
        fetchPPEComplianceData,
        getMockDetectionBarChartData,
        getMockChartModalData
    } from "$lib/api/stats";
    import { chartPreferences } from "$lib/stores/chartPreferences";

    import { Settings, Download, Car, TriangleAlert, Ban, Users, FileText, ZoomIn, SlidersVertical, Camera } from "lucide-svelte";
    // ============================================
    // DATA SOURCE CONFIGURATION
    // ============================================
    // Set this to false to use mock data for charts
    const USE_REAL_DATA = true;

    let now = $state(new Date());
    let interval: any;

    // Auto-subscribe to chart preferences store using Svelte 5 rune
    let preferences = $derived($chartPreferences);
    let selectedRange = $state<TimeRangeOption>('week');
    let customTimeRange = $state<TimeRange | null>(null);

    // Track previous time range to detect changes
    let previousRange = $state<TimeRangeOption | null>(null);
    let previousCustomRange = $state<TimeRange | null>(null);
    let isLoadingTimeRangeChange = $state(false);

    // Watch for store changes and handle time range updates
    $effect(() => {
        const currentRange = preferences.selectedRange;
        const currentCustom = preferences.customTimeRange;

        // Skip initial run
        if (previousRange === null) {
            previousRange = currentRange;
            previousCustomRange = currentCustom;
            selectedRange = currentRange;
            customTimeRange = currentCustom;
            return;
        }

        // Only reload if time range changed (not checkbox changes)
        if (previousRange !== currentRange ||
            JSON.stringify(previousCustomRange) !== JSON.stringify(currentCustom)) {

            // Update state first
            selectedRange = currentRange;
            customTimeRange = currentCustom;
            previousRange = currentRange;
            previousCustomRange = currentCustom;

            // Set loading flag to prevent chart updates until new data arrives
            isLoadingTimeRangeChange = true;
            isChartDataLoading = true;

            // Load new data
            loadChartData().finally(() => {
                isLoadingTimeRangeChange = false;
                isChartDataLoading = false;
            });
        }
    });

    let activeTab = $state<'dashboard' | 'area'>('dashboard');

    let config = $state<Config | null>(null);
    let configLoading = $state(true);
    let systemRunning = $state(false);

    let stats = $state<DashboardStats>({
        detectedPersons: 0,
        detectedVehicles: 0,
        ppeBreaches: 0,
        helmetBreaches: 0,
        vestBreaches: 0,
        riskZoneEntries: 0,
        zoneEntryBreakdown: new Map()
    });
    let statsLoading = $state(false);

    // Create zone breakdown items for StatCardMulti
    let zoneBreakdownItems = $derived(() => {
        if (!config || !stats.zoneEntryBreakdown) return [];

        const items: Array<{label: string; value: number; color?: string}> = [];
        const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-purple-500', 'bg-pink-500'];
        let colorIndex = 0;

        stats.zoneEntryBreakdown.forEach((count, zoneId) => {
            // Find zone by ID
            const zone = config?.zones.find(z => z.zone_id === zoneId);

            // Zone names are now preserved when updating config
            const zoneName = zone?.name || `Zone ${zoneId}`;

            items.push({
                label: zoneName,
                value: count,
                color: colors[colorIndex % colors.length]
            });
            colorIndex++;
        });

        // Sort by value descending to show most active zones first
        return items.sort((a, b) => b.value - a.value);
    });

    // Chart data with all 4 series
    let chartLabels = $state<string[]>([]);
    let personsData = $state<number[]>([]);
    let vehiclesData = $state<number[]>([]);
    let ppeBreachesData = $state<number[]>([]);
    let zoneEntriesData = $state<number[]>([]);
    let chartDataVersion = $state(0); // Increment this to force chart re-render
    let isChartDataLoading = $state(false); // Prevent updates during loading
    let earliestEventTime = $state<Date | null>(null); // Store earliest event for "All" time range

    // Control whether chart updates should animate
    let shouldAnimateCharts = $state(false);

    // Dynamically build datasets based on checkbox preferences and chart type
    // NOTE: Must use structuredClone to break Svelte reactivity and avoid Chart.js conflicts
    let chartDatasets = $derived(() => {
        const datasets = [];
        const isLine = preferences.chartType === 'line';

        if (preferences.showPersons) {
            datasets.push({
                label: 'Persons',
                data: [...personsData], // Break reactivity with spread
                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                borderColor: 'rgb(59, 130, 246)',
                borderWidth: 2,
                fill: isLine ? false : true,
                tension: isLine ? 0.4 : 0
            });
        }
        if (preferences.showVehicles) {
            datasets.push({
                label: 'Vehicles',
                data: [...vehiclesData], // Break reactivity with spread
                backgroundColor: 'rgba(34, 197, 94, 0.7)',
                borderColor: 'rgb(34, 197, 94)',
                borderWidth: 2,
                fill: isLine ? false : true,
                tension: isLine ? 0.4 : 0
            });
        }
        if (preferences.showPPEBreaches) {
            datasets.push({
                label: 'PPE Breaches',
                data: [...ppeBreachesData], // Break reactivity with spread
                backgroundColor: 'rgba(251, 146, 60, 0.7)',
                borderColor: 'rgb(251, 146, 60)',
                borderWidth: 2,
                fill: isLine ? false : true,
                tension: isLine ? 0.4 : 0
            });
        }
        if (preferences.showZoneEntries) {
            datasets.push({
                label: 'Zone Entries',
                data: [...zoneEntriesData], // Break reactivity with spread
                backgroundColor: 'rgba(239, 68, 68, 0.7)',
                borderColor: 'rgb(239, 68, 68)',
                borderWidth: 2,
                fill: isLine ? false : true,
                tension: isLine ? 0.4 : 0
            });
        }
        return datasets;
    });

    let ppeComplianceData = $state<PPEComplianceData>({
        compliant: 0,
        missingHardHat: 0,
        missingVest: 0,
        missingBoth: 0
    });

    // Normalize zones for ZoneDrawer (convert absolute coordinates to 0-1 range if needed)
    function normalizeZones(zones: any[], imageWidth: number, imageHeight: number) {
        if (!zones || zones.length === 0) return [];

        return zones.map(zone => ({
            ...zone,
            points: zone.points.map((p: any) => ({
                x: p.x > 1 ? p.x / imageWidth : p.x,
                y: p.y > 1 ? p.y / imageHeight : p.y
            }))
        }));
    }

    let lastFetchTime = $state<Date | null>(null);
    let pollingInterval: any;
    let isInitialLoadComplete = $state(false);

    // Event cache to avoid re-fetching data when switching time periods
    interface EventCache {
        locationId: number;
        events: Event[];
        fetchTime: Date;
        timeRange: TimeRange;
    }
    let eventCache = $state<EventCache | null>(null);

    // Check if cached data is still valid for the requested time range
    function isCacheValid(locationId: number, requestedRange: TimeRange): boolean {
        if (!eventCache || eventCache.locationId !== locationId) {
            return false;
        }

        // Check if cached time range covers the requested range
        const cacheStart = eventCache.timeRange.start.getTime();
        const cacheEnd = eventCache.timeRange.end.getTime();
        const requestStart = requestedRange.start.getTime();
        const requestEnd = requestedRange.end.getTime();

        // Cache is valid if it covers or equals the requested range
        return cacheStart <= requestStart && cacheEnd >= requestEnd;
    }

    // Filter cached events to the requested time range
    function filterCachedEvents(requestedRange: TimeRange): Event[] {
        if (!eventCache) return [];

        return eventCache.events.filter(event => {
            const eventTime = new Date(event.time).getTime();
            return eventTime >= requestedRange.start.getTime() &&
                   eventTime <= requestedRange.end.getTime();
        });
    }

    // Clear cache and earliest event time when location changes
    $effect(() => {
        if (config?.locationId !== eventCache?.locationId) {
            eventCache = null;
            earliestEventTime = null;
        }
    });

    onMount(() => {
        interval = setInterval(() => {
            now = new Date();
        }, 1000);

        // Start with initial data load
        initialLoad();

        // Start polling every 5 seconds after initial load (only for real data)
        pollingInterval = setInterval(async () => {
            if (isInitialLoadComplete && USE_REAL_DATA) {
                loadStatistics(false, true); // Update stats - force refresh to get new events
                updateChartDataSilently(); // Update chart data without animation
                systemRunning = await getSystemStatus(); // Update system status
            }
        }, 5000);

        return () => {
            clearInterval(interval);
            clearInterval(pollingInterval);
        };
    });

    async function initialLoad() {
        try {
            configLoading = true;
            statsLoading = true;

            // Load configuration and system status
            config = await fetchCurrentConfig();
            systemRunning = await getSystemStatus();
            console.log("Loaded config:", $state.snapshot(config));
            console.log("System running:", systemRunning);
            configLoading = false;

            // If we have a location ID, fetch all data in one go
            if (config && config.locationId) {
                await loadDataForLocation(config.locationId, true);
            } else {
                // No config - just load mock/empty data
                statsLoading = false;
                loadChartData(); // Will use mock data
            }

            isInitialLoadComplete = true;
        } catch (error) {
            console.error("Error during initial load:", error);
            config = null;
            configLoading = false;
            statsLoading = false;
            isInitialLoadComplete = true;
        }
    }

    async function loadDataForLocation(locationId: number, isInitialLoad = false, animate = true, useCache = true) {
        try {
            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined, earliestEventTime || undefined);

            // Check if we should use mock data
            if (!USE_REAL_DATA) {
                console.log('🎭 Loading MOCK data in loadDataForLocation...');
                const mockData = getMockChartModalData(timeRange);
                const ppeData = await fetchPPEComplianceData();

                // Generate mock stats from the mock data
                const mockStats = {
                    detectedPersons: Math.floor(Math.random() * 100) + 50,
                    detectedVehicles: Math.floor(Math.random() * 50) + 20,
                    ppeBreaches: Math.floor(Math.random() * 30) + 10,
                    helmetBreaches: Math.floor(Math.random() * 20) + 5,
                    vestBreaches: Math.floor(Math.random() * 20) + 5,
                    riskZoneEntries: Math.floor(Math.random() * 40) + 15
                };

                shouldAnimateCharts = animate;
                chartLabels = mockData.labels;
                personsData = mockData.persons;
                vehiclesData = mockData.vehicles;
                ppeBreachesData = mockData.ppeBreaches;
                zoneEntriesData = mockData.zoneEntries;
                stats = mockStats;
                ppeComplianceData = ppeData;
                chartDataVersion++;
                lastFetchTime = new Date();
                statsLoading = false;
                return;
            }

            // If "all" range is selected and we don't have earliest time yet, fetch it first
            if (selectedRange === 'all' && !earliestEventTime && USE_REAL_DATA) {
                // Fetch with fallback range to get all events
                const fallbackRange = calculateTimeRange('all', undefined);
                const allEventsResponse = await fetchEventsForLocation(locationId, fallbackRange);
                if (allEventsResponse.events.length > 0) {
                    earliestEventTime = findEarliestEventTime(allEventsResponse.events);
                    console.log(`📅 Found earliest event: ${earliestEventTime?.toISOString()}`);
                }
            }

            let events: Event[];

            // Check if we can use cached data
            if (USE_REAL_DATA && useCache && isCacheValid(locationId, timeRange)) {
                console.log('📦 Using cached events');
                events = filterCachedEvents(timeRange);
            } else {
                // Fetch fresh events from API
                const eventsResponse = await fetchEventsForLocation(locationId, timeRange);
                events = eventsResponse.events;

                console.log(`✅ Fetched ${events.length} events from API`);

                // Update cache with the broader time range for future use
                // For day/week, we fetch and cache a month worth of data
                // For month, we cache the month
                // For all time, we cache what we get
                let cacheTimeRange = timeRange;
                if (selectedRange === 'day' || selectedRange === 'week') {
                    // Cache a month's worth of data when viewing day or week
                    const cacheStart = new Date(timeRange.start);
                    cacheStart.setDate(1); // Start of month
                    cacheStart.setHours(0, 0, 0, 0);
                    const cacheEnd = new Date(cacheStart);
                    cacheEnd.setMonth(cacheEnd.getMonth() + 1);
                    cacheEnd.setDate(0); // Last day of month
                    cacheEnd.setHours(23, 59, 59, 999);

                    // If we're viewing a different range, fetch the broader data
                    if (cacheStart.getTime() < timeRange.start.getTime() ||
                        cacheEnd.getTime() > timeRange.end.getTime()) {
                        const broadResponse = await fetchEventsForLocation(locationId, {
                            start: cacheStart,
                            end: cacheEnd
                        });
                        eventCache = {
                            locationId,
                            events: broadResponse.events,
                            fetchTime: new Date(),
                            timeRange: { start: cacheStart, end: cacheEnd }
                        };
                        console.log(`📦 Cached ${broadResponse.events.length} events for month range`);
                        // Filter to requested range
                        events = filterCachedEvents(timeRange);
                    } else {
                        eventCache = {
                            locationId,
                            events,
                            fetchTime: new Date(),
                            timeRange
                        };
                    }
                } else {
                    // Cache the exact range for month/all time views
                    eventCache = {
                        locationId,
                        events,
                        fetchTime: new Date(),
                        timeRange
                    };
                }
            }

            console.log(`✅ Fetched ${events.length} events from API`);

            // Calculate all data transformations first (without updating state)
            const newStats = calculateStatsFromEvents(events);
            if (isInitialLoad) {
                console.log("Loaded initial stats from events:", $state.snapshot(newStats));
            }

            const fullChartData = createChartDataFromEvents(events, timeRange);
            const ppeData = calculatePPEComplianceFromEvents(events);

            // Generate proper labels from timestamps
            const hoursDiff = Math.floor((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60));
            const newChartLabels = fullChartData.persons.map(point => {
                const date = new Date(point.timestamp);

                if (hoursDiff <= 24) {
                    // Day view - show hours
                    return `${date.getHours()}:00`;
                } else if (hoursDiff <= 168) {
                    // Week view - show day names with dates
                    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    return `${days[date.getDay()]} ${months[date.getMonth()]} ${date.getDate()}`;
                } else if (hoursDiff <= 720) {
                    // Month view - show dates
                    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    return `${months[date.getMonth()]} ${date.getDate()}`;
                } else {
                    // All time - show week date ranges
                    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                    const weekEnd = new Date(date.getTime() + (6 * 24 * 60 * 60 * 1000)); // Add 6 days
                    const startMonth = months[date.getMonth()];
                    const endMonth = months[weekEnd.getMonth()];

                    if (date.getMonth() === weekEnd.getMonth()) {
                        // Same month: "Oct 1-7"
                        return `${startMonth} ${date.getDate()}-${weekEnd.getDate()}`;
                    } else {
                        // Different months: "Oct 28-Nov 3"
                        return `${startMonth} ${date.getDate()}-${endMonth} ${weekEnd.getDate()}`;
                    }
                }
            });

            // Batch update all state at once using untrack to prevent intermediate renders
            shouldAnimateCharts = animate;

            // Update chart data atomically
            chartLabels = newChartLabels;
            personsData = fullChartData.persons.map(point => point.value);
            vehiclesData = fullChartData.vehicles.map(point => point.value);
            ppeBreachesData = fullChartData.ppeBreaches.map(point => point.value);
            zoneEntriesData = fullChartData.zoneEntries.map(point => point.value);

            // Update other data
            stats = newStats;
            ppeComplianceData = ppeData; // Always update pie chart data

            // Increment version to signal complete data update
            chartDataVersion++;

            lastFetchTime = new Date();
            statsLoading = false;
        } catch (error) {
            console.error("Error loading data:", error);
            stats = {
                detectedPersons: 0,
                detectedVehicles: 0,
                ppeBreaches: 0,
                helmetBreaches: 0,
                vestBreaches: 0,
                riskZoneEntries: 0
            };
            statsLoading = false;
        }
    }

    async function loadStatistics(isInitialLoad = false, forceRefresh = false) {
        // Skip polling if using mock data
        if (!USE_REAL_DATA) {
            return;
        }

        if (!config?.locationId) {
            console.log("No location ID available for stats");
            return;
        }

        statsLoading = true;
        try {
            await loadDataForLocation(config.locationId, isInitialLoad, false, !forceRefresh);
        } catch (error) {
            console.error("Error loading statistics:", error);
            statsLoading = false;
        }
    }

    async function loadChartData() {
        try {
            // Enable animations for intentional loads (initial/time period change)
            shouldAnimateCharts = true;

            if (USE_REAL_DATA && config?.locationId) {
                // Use the shared data loading function
                await loadDataForLocation(config.locationId, false, true);
            } else {
                // ============================================
                // MOCK DATA (Fallback or when USE_REAL_DATA = false)
                // ============================================
                console.log('🎭 Loading MOCK data...', {
                    reason: !USE_REAL_DATA ? 'USE_REAL_DATA is false' :
                            !config ? 'No config loaded' :
                            !config.locationId ? 'No locationId in config' :
                            'Unknown'
                });

                const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined);
                const mockData = getMockChartModalData(timeRange);
                const ppeData = await fetchPPEComplianceData();

                // Store all data series
                chartLabels = mockData.labels;
                personsData = mockData.persons;
                vehiclesData = mockData.vehicles;
                ppeBreachesData = mockData.ppeBreaches;
                zoneEntriesData = mockData.zoneEntries;

                // PPE compliance data (pie chart) - always show
                ppeComplianceData = ppeData;

                // Increment version to signal complete data update
                chartDataVersion++;
            }
        } catch (error) {
            console.error("Error loading chart data:", error);
            // Fallback to mock data on error
            const timeRange = calculateTimeRange(selectedRange, customTimeRange || undefined);
            const mockData = getMockChartModalData(timeRange);
            chartLabels = mockData.labels;
            personsData = mockData.persons;
            vehiclesData = mockData.vehicles;
            ppeBreachesData = mockData.ppeBreaches;
            zoneEntriesData = mockData.zoneEntries;
        }
    }

    // Silent update for polling - updates data without triggering chart reinit/animation
    async function updateChartDataSilently() {
        // Skip polling if using mock data
        if (!USE_REAL_DATA) {
            return;
        }

        if (!config?.locationId) {
            return;
        }

        try {
            // Disable animations for polling updates
            shouldAnimateCharts = false;
            await loadDataForLocation(config.locationId, false, false);
        } catch (error) {
            console.error("Error updating chart data:", error);
            // On error, keep existing data
        }
    }

    // Modal state
    let showSettingsModal = $state(false);
    let showConfigModal = $state(false);
    let showLogModal = $state(false);
    let showDateRangePicker = $state(false);
    let showChartModal = $state(false);
    let showZoneBreakdownModal = $state(false);
    let chartModalTitle = $state('Chart Details');

    function openSettingsModal() {
        showSettingsModal = true;
    }
    function closeSettingsModal() {
        showSettingsModal = false;
    }
    function openConfigModal() {
        showConfigModal = true;
    }
    function closeConfigModal() {
        showConfigModal = false;
        // Reload configuration and data after modal closes to reflect any changes
        initialLoad();
    }
    function openLogModal() {
        showLogModal = true;
    }
    function closeLogModal() {
        showLogModal = false;
    }
    function openDateRangePicker() {
        showDateRangePicker = true;
    }
    function closeDateRangePicker() {
        showDateRangePicker = false;
    }
    function openZoneBreakdownModal() {
        showZoneBreakdownModal = true;
    }
    function closeZoneBreakdownModal() {
        showZoneBreakdownModal = false;
    }
    function handleDateRangeApply(start: Date, end: Date) {
        customTimeRange = { start, end };
        selectedRange = 'custom';
        // Update global store
        chartPreferences.set({
            ...preferences,
            selectedRange: 'custom',
            customTimeRange: { start, end }
        });
        // Reload stats with new custom range
        lastFetchTime = null;
        loadStatistics(true);
    }

    function openChartModal(title: string) {
        chartModalTitle = title;
        showChartModal = true;
    }

    function closeChartModal() {
        showChartModal = false;
    }

    const ranges: { label: string; value: TimeRangeOption }[] = [
        { label: "Today", value: "day" },
        { label: "This Week", value: "week" },
        { label: "This Month", value: "month" },
        { label: "All", value: "all" },
        { label: "Custom Date", value: "custom" }
    ];

    function selectRange(val: TimeRangeOption) {
        const rangeChanged = selectedRange !== val;
        selectedRange = val;
        // If custom is selected, open the date picker
        if (val === 'custom') {
            openDateRangePicker();
        } else {
            customTimeRange = null;
            // Update global store
            chartPreferences.set({
                ...preferences,
                selectedRange: val,
                customTimeRange: null
            });
            // Reload stats if range actually changed
            if (rangeChanged && config?.locationId) {
                lastFetchTime = null;
                loadStatistics(true);
            }
        }
    }

</script>

<header class="w-full bg-gray-50" style="height: clamp(4rem, 20vh, 20rem);">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-full">
        <!-- Left: Tab Navigation -->
        <div class="flex gap-1 lg:gap-2 bg-white p-1 rounded-lg shadow-sm">
            <button
                class="px-4 lg:px-6 py-1.5 lg:py-2 rounded-md font-semibold transition text-sm lg:text-base
                    {activeTab === 'dashboard'
                        ? 'bg-[#E76A23] text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'}"
                onclick={() => activeTab = 'dashboard'}
            >
                Dashboard
            </button>
            <button
                class="px-4 lg:px-6 py-1.5 lg:py-2 rounded-md font-semibold transition text-sm lg:text-base
                    {activeTab === 'area'
                        ? 'bg-[#E76A23] text-white'
                        : 'bg-white text-gray-700 hover:bg-gray-50'}"
                onclick={() => activeTab = 'area'}
            >
                Area Management
            </button>
        </div>

        <!-- Right: Settings -->
        <div class="flex items-center gap-1 lg:gap-3">
            {#if !config || !systemRunning}
                <!-- Show setup button if no config or system not running -->
                <button
                    class="px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg bg-[#E76A23] text-white hover:bg-[#d15e1e] transition font-medium shadow-sm flex items-center gap-2 text-xs lg:text-sm"
                    onclick={openConfigModal}
                    aria-label="Setup Configuration"
                >
                    <SlidersVertical class="h-4 w-4 lg:h-5 lg:w-5" />
                    Setup
                </button>
            {:else}
                <!-- Show running config status -->
                <button
                    class="flex items-center gap-2 px-3 lg:px-4 py-1.5 lg:py-2 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition cursor-pointer"
                    onclick={openConfigModal}
                    aria-label="View Configuration"
                >
                    <div class="relative flex items-center">
                        <div class="w-2 h-2 lg:w-2.5 lg:h-2.5 bg-green-500 rounded-full animate-pulse"></div>
                        <div class="absolute w-2 h-2 lg:w-2.5 lg:h-2.5 bg-green-500 rounded-full opacity-75"></div>
                    </div>
                    <span class="text-xs lg:text-sm font-medium text-green-900">{config.locationName}</span>
                </button>
            {/if}
            <button class="p-1.5 lg:p-2 rounded-full hover:bg-gray-100 transition" aria-label="Export">
                <Download size={20} class="lg:w-6 lg:h-6 text-gray-600" />
            </button>
            <button class="p-1.5 lg:p-2 rounded-full hover:bg-gray-100 transition" aria-label="Settings" onclick={openSettingsModal}>
                <Settings size={20} class="lg:w-6 lg:h-6 text-gray-600" />
            </button>
        </div>
    </div>
</header>

<Modal open={showSettingsModal} onClose={closeSettingsModal} modalClass="p-6 w-full max-w-md max-h-[90vh]">
    <div class="w-full">
        <h2 class="text-xl font-semibold text-gray-800 mb-6">Settings</h2>
        <div class="space-y-4">
            <button
                class="w-full px-4 py-3 bg-[#E76A23] text-white rounded-lg hover:bg-[#d15e1e] transition font-medium shadow-sm flex items-center justify-center gap-2"
                onclick={openLogModal}
            >
                <FileText class="h-5 w-5" />
                    View Logs
                </button>
            </div>
        </div>
    </Modal>

<!-- MAIN CONTENT -->
<main class="bg-gray-50" style="min-height: calc(100vh - clamp(4rem, 6vh, 6rem));">
    {#if activeTab === 'dashboard'}
        <!-- Time Range Selector (below header, only for dashboard) -->
        <div style="padding: clamp(0.5rem, 1.5vh, 1rem) 0;">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap gap-2">
                {#each ranges as r}
                    <button
                        class="px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg font-semibold transition text-xs lg:text-sm
                            {selectedRange === r.value
                                ? 'bg-[#E76A23] text-white'
                                : 'bg-white text-gray-700 hover:bg-orange-50 border border-gray-200'}"
                        onclick={() => selectRange(r.value)}
                    >
                        {r.label}
                    </button>
                {/each}
                {#if selectedRange === 'custom' && customTimeRange}
                    <span class="flex items-center text-xs lg:text-sm text-gray-600 ml-2 px-2 lg:px-3 py-1 bg-orange-50 rounded-full border border-orange-200">
                        {customTimeRange.start.toLocaleDateString('sv-SE')} - {customTimeRange.end.toLocaleDateString('sv-SE')}
                    </span>
                {/if}
            </div>
        </div>

        <!-- Dashboard Content -->
        <div class="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto" style="padding-top: clamp(0.5rem, 1vh, 1.5rem); padding-bottom: clamp(0.5rem, 1vh, 1.5rem);">
            <!-- Cards Row -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-4" style="grid-auto-rows: clamp(85px, 14vh, 130px);">
        <StatCard
            title="Detected Persons"
            value={stats.detectedPersons}
            iconColor="text-[#E76A23]"
            icon={Users}
        />

        <StatCard
            title="Detected Vehicles"
            value={stats.detectedVehicles}
            iconColor="text-green-600"
            icon={Car}
        />

        <StatCard
            title="PPE Compliance Breaches"
            value={stats.ppeBreaches}
            iconColor="text-orange-600"
            icon={TriangleAlert}
        />

        <StatCardMulti
            title="Risk Zone Entries"
            totalValue={stats.riskZoneEntries}
            items={zoneBreakdownItems()}
            iconColor="text-red-600"
            icon={Ban}
            onclick={openZoneBreakdownModal}
        />
    </div>

    <!-- Charts Row (2 charts only) -->
    <div class="grid grid-cols-1 lg:grid-cols-2" style="gap: clamp(0.75rem, 1.5vh, 1.5rem); height: clamp(240px, 34vh, 420px);">
        <!-- Detection Bar Chart - Persons & Vehicles -->
        <div
            class="bg-white rounded-2xl shadow flex flex-col cursor-pointer hover:shadow-xl transition-shadow duration-200 group h-full"
            style="padding: clamp(0.75rem, 1.5vh, 1.5rem);"
            onclick={() => openChartModal('Detections Over Time')}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && openChartModal('Detections Over Time')}
        >
            <div class="flex items-center justify-between" style="margin-bottom: clamp(0.5rem, 1vh, 1rem);">
                <h3 class="text-base xl:text-lg font-semibold text-gray-700">Detections Over Time</h3>
                <ZoomIn class="w-4 h-4 xl:w-5 xl:h-5 text-gray-400 group-hover:text-[#E76A23] transition-colors" />
            </div>
            <div class="flex-1">
                {#if !isChartDataLoading}
                    {#if preferences.chartType === 'bar'}
                    {#key chartDataVersion}
                    <BarChart
                        labels={[...chartLabels]}
                        datasets={chartDatasets()}
                        animate={shouldAnimateCharts}
                    />
                    {/key}
                    {:else if preferences.chartType === 'line'}
                    {#key chartDataVersion}
                    <LineChart
                        data={{
                            labels: [...chartLabels],
                            datasets: chartDatasets()
                        }}
                        animate={shouldAnimateCharts}
                    />
                    {/key}
                    {:else}
                    <div class="text-gray-400 text-sm">Unknown chart type: {preferences.chartType}</div>
                    {/if}
                {:else}
                <div class="flex items-center justify-center h-full">
                    <div class="text-gray-400">Loading...</div>
                </div>
                {/if}
            </div>
            <p class="text-xs text-gray-500 text-center opacity-0 group-hover:opacity-100 transition-opacity" style="margin-top: clamp(0.5rem, 1vh, 0.75rem);">
                Click to expand and customize
            </p>
        </div>

        <!-- PPE Compliance Pie Chart -->
        <div class="bg-white rounded-2xl shadow flex flex-col h-full" style="padding: clamp(0.75rem, 1.5vh, 1.5rem);">
            <div class="flex items-center justify-between" style="margin-bottom: clamp(0.5rem, 1vh, 1rem);">
                <h3 class="text-base xl:text-lg font-semibold text-gray-700">PPE Compliance Breakdown</h3>
            </div>
            <div class="flex-1">
                <PieChart
                    labels={['Compliant', 'Missing Hard Hat', 'Missing Vest', 'Missing Both']}
                    data={[
                        ppeComplianceData.compliant,
                        ppeComplianceData.missingHardHat,
                        ppeComplianceData.missingVest,
                        ppeComplianceData.missingBoth
                    ]}
                    backgroundColor={[
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(251, 146, 60, 0.8)',
                        'rgba(234, 179, 8, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ]}
                    isDoughnut={true}
                    animate={shouldAnimateCharts}
                />
            </div>
        </div>
    </div>
        </div>
    {:else if activeTab === 'area'}
        <!-- Area Management Content -->
        <div class="px-4 sm:px-6 lg:px-8 py-4 lg:py-6 max-w-7xl mx-auto">
            <div class="mb-6">
                <h2 class="text-2xl font-bold text-gray-800">Area Management</h2>
            </div>

            <!-- Snapshot with Zones -->
            <div class="bg-white rounded-2xl shadow p-6">
                <h3 class="text-lg font-semibold text-gray-700 mb-4">Camera View with Zones</h3>
                <div class="p-4 flex items-center justify-center bg-gray-100 rounded-lg">
                    {#if config && config.snapshotPath}
                        <div class="w-full max-w-4xl max-h-full">
                            <ZoneDrawer
                                zones={normalizeZones(config.zones || [], 1920, 1080)}
                                imageSrc={config.snapshotPath}
                                width={1200}
                                height={675}
                                readOnly={true}
                                onFinishZone={() => {}}
                            />
                        </div>
                    {:else}
                        <div class="text-center">
                            <Camera class="h-20 w-20 text-gray-300 mx-auto mb-4" />
                            <p class="text-gray-500 text-lg font-medium mb-2">No snapshot available</p>
                            <p class="text-gray-400 text-sm">Configure camera settings to capture a snapshot</p>
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    {/if}

    <ConfigSetupModal
        open={showConfigModal}
        onClose={closeConfigModal}
    />

    <LogModal
        open={showLogModal}
        onClose={closeLogModal}
    />

    <DateRangePicker
        open={showDateRangePicker}
        onClose={closeDateRangePicker}
        onApply={handleDateRangeApply}
    />

    <ZoneBreakdownModal
        open={showZoneBreakdownModal}
        onClose={closeZoneBreakdownModal}
        items={zoneBreakdownItems()}
        totalEntries={stats.riskZoneEntries}
    />

    <ChartModal
        bind:open={showChartModal}
        onClose={closeChartModal}
        chartType={preferences.chartType}
        initialTitle={chartModalTitle}
        locationId={config?.locationId}
    />
</main>

<style>
    :global(body) {
        background: #f9fafb;
    }
</style>
