<script lang="ts">
    import Modal from "./modal.svelte";
    import ZoneDrawer from "./ZoneDrawer.svelte";
    import {
        fetchCurrentConfig,
        fetchAllLocations,
        fetchConfigByLocation,
        deleteCurrentConfig,
        deleteLocationConfig,
        saveConfig,
        fetchSnapshot,
        startSystem,
        stopSystem,
        activateLocation,
        type Zone,
        type Config,
        type LocationSummary
    } from "$lib/api/config";

    export let open: boolean = false;
    export let onClose: () => void = () => {};

    let currentStep = 1;
    let locationName = "";
    let zones: Zone[] = [];

    // Stored configuration state
    let storedConfig: Config | null = null;
    let allLocations: LocationSummary[] = [];
    let selectedLocationId: number | null = null;
    let isEditingExisting = false;
    let showNewLocationForm = false;
    let viewMode: "list" | "view" | "edit" = "list"; // New view mode state

    // Snapshot state
    let snapshotLoading = false;
    let snapshotError: string | null = null;
    let customSnapshotPath: string = '';

    // Load stored configuration when modal opens
    $: if (open) {
        loadStoredConfig();
        loadAllLocations();
        viewMode = "list"; // Reset to list view
    }

    async function loadStoredConfig() {
        storedConfig = await fetchCurrentConfig();
    }

    async function loadAllLocations() {
        allLocations = await fetchAllLocations();
    }

    async function selectLocation(locationId: number) {
        const config = await fetchConfigByLocation(locationId);
        if (config) {
            selectedLocationId = locationId;
            locationName = config.locationName;
            zones = [...config.zones];
            customSnapshotPath = config.snapshotPath || '';
            viewMode = "view"; // Show view mode first
        }
    }

    async function editLocation() {
        // If editing the current running location, stop the system first
        if (storedConfig && selectedLocationId === storedConfig.locationId) {
            const confirmed = confirm("Editing this configuration will stop the monitoring system. Continue?");
            if (!confirmed) return;

            await stopSystem();
            console.log("System stopped for editing");
        }

        isEditingExisting = true;
        viewMode = "edit";
        currentStep = 2; // Go to zones step
    }

    async function makeLocationActive(locationId: number) {
        const success = await activateLocation(locationId);
        if (success) {
            await startSystem();
            await loadStoredConfig();
            await loadAllLocations();
            console.log("Location activated and system started");
            // Return to list view to show the new active location
            viewMode = "list";
        } else {
            alert("Failed to activate location");
        }
    }

    function loadExistingConfig() {
        if (storedConfig) {
            selectedLocationId = storedConfig.locationId;
            locationName = storedConfig.locationName;
            zones = [...storedConfig.zones];
            customSnapshotPath = storedConfig.snapshotPath || '';
            viewMode = "view"; // Show view mode first
        }
    }

    function startNewLocation() {
        showNewLocationForm = true;
        selectedLocationId = null;
        locationName = "";
        zones = [];
        customSnapshotPath = "";
        isEditingExisting = false;
        viewMode = "edit";
    }

    async function removeSelectedLocation(locationId: number) {
        if (confirm("Are you sure you want to delete this location and all its zones?")) {
            const success = await deleteLocationConfig(locationId);
            if (success) {
                await loadAllLocations();
                await loadStoredConfig(); // Refresh stored config
                if (selectedLocationId === locationId) {
                    selectedLocationId = null;
                    locationName = "";
                    zones = [];
                    customSnapshotPath = "";
                    viewMode = "list";
                }
            }
        }
    }

    async function loadSnapshot() {
        if (!locationName.trim()) {
            snapshotError = "Please enter a location name first";
            return;
        }

        snapshotLoading = true;
        snapshotError = null;
        customSnapshotPath = await fetchSnapshot();
        snapshotLoading = false;
    }

    const steps = [
        { id: 1, title: "Setup", description: "Current or new configuration" },
        { id: 2, title: "Zones", description: "Define monitoring zones" },
        { id: 3, title: "Summary", description: "Review configuration" }
    ];

    function nextStep() {
        if (currentStep < 3) {
            currentStep += 1;
        }
    }

    function prevStep() {
        if (currentStep > 1) {
            currentStep -= 1;
            if (currentStep === 1) {
                isEditingExisting = false;
                showNewLocationForm = false;
                viewMode = "list";
            }
        }
    }

    function goToStep(step: number) {
        currentStep = step;
        if (step === 1) {
            isEditingExisting = false;
            showNewLocationForm = false;
            viewMode = "list";
        }
    }

    function backToList() {
        viewMode = "list";
        selectedLocationId = null;
        locationName = "";
        zones = [];
        customSnapshotPath = "";
        isEditingExisting = false;
        showNewLocationForm = false;
        currentStep = 1;
    }

    function handleFinishZone(points: { x: number; y: number }[], name: string) {
        zones = [...zones, { points, name }];
    }

    function resetConfig() {
        currentStep = 1;
        locationName = "";
        zones = [];
        customSnapshotPath = "";
        isEditingExisting = false;
        showNewLocationForm = false;
        selectedLocationId = null;
        viewMode = "list";
    }

    function handleClose() {
        resetConfig();
        onClose();
    }

    async function handleStart() {
        try {
            const success = await saveConfig(locationName, zones);

            if (success) {
                console.log("Configuration sent successfully");

                let startResult = await startSystem();
                console.log("System start response:", startResult);

                handleClose();
            } else {
                alert("Failed to setup configuration");
            }
        } catch (error: any) {
            console.error("Error setting up configuration:", error);
            alert(`Error: ${error.message}`);
        }
    }

    $: canProceedStep1 = locationName.trim().length > 0;
    $: canProceedStep2 = true;
</script>

<Modal {open} onClose={handleClose} modalClass="p-0 w-full max-w-4xl max-h-[90vh] flex flex-col">
    <div class="w-full flex flex-col h-full min-h-0">
        <!-- Header with Steps - only show during setup flow -->
        {#if (showNewLocationForm || isEditingExisting) && viewMode === "edit"}
            <div class="border-b border-gray-200 px-6 py-4 flex-shrink-0">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Setup Configuration</h2>

                <!-- Step Indicators -->
                <div class="flex items-center space-x-4">
                {#each steps as step, index}
                    <div class="flex items-center">
                        <button
                            class="flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-colors
                                {currentStep === step.id
                                    ? 'bg-blue-600 text-white'
                                    : currentStep > step.id
                                        ? 'bg-green-500 text-white'
                                        : 'bg-gray-200 text-gray-600'}"
                            on:click={() => goToStep(step.id)}
                            disabled={step.id > 1 && !canProceedStep1 || step.id > 2 && !canProceedStep2}
                        >
                            {#if currentStep > step.id}
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                </svg>
                            {:else}
                                {step.id}
                            {/if}
                        </button>
                        <div class="ml-3">
                            <p class="text-sm font-medium text-gray-900">{step.title}</p>
                            <p class="text-xs text-gray-500">{step.description}</p>
                        </div>
                        {#if index < steps.length - 1}
                            <div class="w-12 h-px bg-gray-300 mx-4"></div>
                        {/if}
                    </div>
                {/each}
                </div>
            </div>
        {/if}

        <!-- Content Area -->
        <div class="flex-1 min-h-0 overflow-hidden flex flex-col">
            {#if viewMode === "list"}
                <!-- List Mode: Show all locations -->
                <div class="flex-1 overflow-y-auto px-6 py-8">
                    <div class="max-w-3xl mx-auto">
                        <div class="text-center mb-6">
                            <h3 class="text-lg font-semibold text-gray-900 mb-2">Choose Configuration</h3>
                            <p class="text-sm text-gray-600">Select an existing location or create a new one</p>
                        </div>

                        <!-- Current Active Location -->
                        {#if storedConfig}
                            <div class="mb-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
                                <div class="flex items-start justify-between">
                                    <div class="flex-1">
                                        <div class="flex items-center gap-2 mb-2">
                                            <span class="px-2 py-1 bg-green-600 text-white text-xs font-semibold rounded">CURRENTLY RUNNING</span>
                                            <h4 class="text-base font-semibold text-gray-900">{storedConfig.locationName}</h4>
                                        </div>
                                        <p class="text-sm text-gray-600 mb-3">
                                            {storedConfig.zones.length} zone{storedConfig.zones.length !== 1 ? 's' : ''} configured
                                        </p>
                                        <div class="flex gap-2">
                                            <button
                                                on:click={loadExistingConfig}
                                                class="px-3 py-1.5 text-xs font-medium rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors"
                                            >
                                                View
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {/if}

                        <!-- All Locations List -->
                        {#if allLocations.length > 0}
                            <div class="mb-6">
                                <h4 class="text-sm font-semibold text-gray-700 mb-3">
                                    {storedConfig ? 'Other Locations' : 'Available Locations'}
                                </h4>
                                <div class="space-y-2 max-h-96 overflow-y-auto">
                                    {#each allLocations as location}
                                        {#if !storedConfig || storedConfig.locationId !== location.locationId}
                                            <div
                                                class="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                                            >
                                                <div class="flex-1">
                                                    <h5 class="text-sm font-medium text-gray-900">{location.locationName}</h5>
                                                    <p class="text-xs text-gray-500">
                                                        {location.zoneCount} zone{location.zoneCount !== 1 ? 's' : ''}
                                                    </p>
                                                </div>
                                                <div class="flex gap-2">
                                                    <button
                                                        on:click={() => selectLocation(location.locationId)}
                                                        class="px-3 py-1.5 text-xs font-medium rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                                                    >
                                                        View
                                                    </button>
                                                    <button
                                                        on:click={() => makeLocationActive(location.locationId)}
                                                        class="px-3 py-1.5 text-xs font-medium rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors"
                                                    >
                                                        Activate
                                                    </button>
                                                    <button
                                                        on:click={() => removeSelectedLocation(location.locationId)}
                                                        class="px-3 py-1.5 text-xs font-medium rounded-md bg-white border border-red-300 text-red-700 hover:bg-red-50 transition-colors"
                                                    >
                                                        Delete
                                                    </button>
                                                </div>
                                            </div>
                                        {/if}
                                    {/each}
                                </div>
                            </div>
                        {/if}

                        <!-- New Location Button -->
                        <button
                            on:click={startNewLocation}
                            class="w-full py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors group"
                        >
                            <div class="flex items-center justify-center gap-2">
                                <svg class="w-5 h-5 text-gray-400 group-hover:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                                </svg>
                                <span class="text-sm font-medium text-gray-600 group-hover:text-blue-600">Create New Location</span>
                            </div>
                        </button>
                    </div>
                </div>
            {:else if viewMode === "view"}
                <!-- View Mode: Display location with snapshot and zones -->
                <div class="flex-1 flex overflow-hidden">
                    <!-- Left Panel: Location Info and Controls -->
                    <div class="w-80 border-r border-gray-200 bg-white p-6 overflow-y-auto flex-shrink-0 flex flex-col">
                        <!-- Header with Back Button -->
                        <div class="mb-6">
                            <button
                                on:click={backToList}
                                class="mb-4 px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors"
                            >
                                <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                                </svg>
                                Back to List
                            </button>

                            <div class="flex items-center gap-2 mb-2">
                                {#if storedConfig && selectedLocationId === storedConfig.locationId}
                                    <span class="px-2 py-1 bg-green-600 text-white text-xs font-semibold rounded">CURRENTLY RUNNING</span>
                                {/if}
                            </div>
                            <h2 class="text-xl font-semibold text-gray-900 mb-1">{locationName}</h2>
                            <p class="text-sm text-gray-600">
                                {zones.length} monitoring zone{zones.length !== 1 ? 's' : ''} configured
                            </p>
                        </div>

                        <!-- Zones List -->
                        <div class="mb-6 flex-1 min-h-0">
                            <h3 class="text-sm font-semibold text-gray-900 mb-3">Monitoring Zones</h3>
                            {#if zones.length > 0}
                                <div class="space-y-2 max-h-64 overflow-y-auto">
                                    {#each zones as zone, i}
                                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                                            <div class="flex items-center gap-2">
                                                <div class="w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                                                    {i + 1}
                                                </div>
                                                <span class="text-sm font-medium text-gray-900">{zone.name}</span>
                                            </div>
                                            <span class="text-xs text-gray-500">{zone.points.length}pts</span>
                                        </div>
                                    {/each}
                                </div>
                            {:else}
                                <p class="text-sm text-gray-600">No zones configured - monitoring entire area</p>
                            {/if}
                        </div>

                        <!-- Action Buttons -->
                        <div class="space-y-2 flex-shrink-0">
                            {#if !storedConfig || selectedLocationId !== storedConfig.locationId}
                                <button
                                    on:click={() => makeLocationActive(selectedLocationId!)}
                                    class="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium shadow-sm flex items-center justify-center gap-2"
                                >
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                    Set as Active
                                </button>
                            {/if}
                            <button
                                on:click={editLocation}
                                class="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium shadow-sm flex items-center justify-center gap-2"
                            >
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                                </svg>
                                Edit
                            </button>
                            <button
                                on:click={() => removeSelectedLocation(selectedLocationId!)}
                                class="w-full px-4 py-3 border border-red-300 bg-white text-red-700 rounded-lg hover:bg-red-50 transition font-medium flex items-center justify-center gap-2"
                            >
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                </svg>
                                Delete
                            </button>
                        </div>
                    </div>

                    <!-- Right Panel: Snapshot Preview -->
                    <div class="flex-1 p-6 flex items-center justify-center bg-gray-100 overflow-auto">
                        {#if customSnapshotPath}
                            <div class="w-full max-w-5xl">
                                <ZoneDrawer
                                    onFinishZone={() => {}}
                                    width={1200}
                                    height={675}
                                    zones={zones}
                                    readOnly={true}
                                    imageSrc={customSnapshotPath}
                                />
                            </div>
                        {:else}
                            <div class="text-center">
                                <svg class="w-20 h-20 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                                <h3 class="text-lg font-medium text-gray-900 mb-2">No Snapshot Available</h3>
                                <p class="text-sm text-gray-600">This location doesn't have a snapshot saved.</p>
                            </div>
                        {/if}
                    </div>
                </div>
            {:else if viewMode === "edit" && currentStep === 1}
                <!-- Step 1: Location Selection -->
                <div class="flex-1 overflow-y-auto px-6 py-8">
                    {#if !showNewLocationForm && !isEditingExisting}
                        <div class="max-w-3xl mx-auto">
                            <div class="text-center mb-6">
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Choose Configuration</h3>
                                <p class="text-sm text-gray-600">Select an existing location or create a new one</p>
                            </div>

                            <!-- Current Active Location -->
                            {#if storedConfig}
                                <div class="mb-6 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
                                    <div class="flex items-start justify-between">
                                        <div class="flex-1">
                                            <div class="flex items-center gap-2 mb-2">
                                                <span class="px-2 py-1 bg-blue-600 text-white text-xs font-semibold rounded">ACTIVE</span>
                                                <h4 class="text-base font-semibold text-gray-900">{storedConfig.locationName}</h4>
                                            </div>
                                            <p class="text-sm text-gray-600 mb-3">
                                                {storedConfig.zones.length} zone{storedConfig.zones.length !== 1 ? 's' : ''} configured
                                            </p>
                                            <div class="flex gap-2">
                                                <button
                                                    on:click={loadExistingConfig}
                                                    class="px-3 py-1.5 text-xs font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                                                >
                                                    View
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            {/if}

                            <!-- All Locations List -->
                            {#if allLocations.length > 0}
                                <div class="mb-6">
                                    <h4 class="text-sm font-semibold text-gray-700 mb-3">Available Locations</h4>
                                    <div class="space-y-2 max-h-96 overflow-y-auto">
                                        {#each allLocations as location}
                                            <div
                                                class="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors
                                                    {storedConfig && storedConfig.locationId === location.locationId ? 'opacity-50' : ''}"
                                            >
                                                <div class="flex-1">
                                                    <h5 class="text-sm font-medium text-gray-900">{location.locationName}</h5>
                                                    <p class="text-xs text-gray-500">
                                                        {location.zoneCount} zone{location.zoneCount !== 1 ? 's' : ''}
                                                    </p>
                                                </div>
                                                <div class="flex gap-2">
                                                    {#if !storedConfig || storedConfig.locationId !== location.locationId}
                                                        <button
                                                            on:click={() => selectLocation(location.locationId)}
                                                            class="px-3 py-1.5 text-xs font-medium rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                                                        >
                                                            View
                                                        </button>
                                                        <button
                                                            on:click={() => removeSelectedLocation(location.locationId)}
                                                            class="px-3 py-1.5 text-xs font-medium rounded-md bg-white border border-red-300 text-red-700 hover:bg-red-50 transition-colors"
                                                        >
                                                            Delete
                                                        </button>
                                                    {/if}
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                </div>
                            {/if}

                            <!-- New Location Button -->
                            <button
                                on:click={startNewLocation}
                                class="w-full py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors group"
                            >
                                <div class="flex items-center justify-center gap-2">
                                    <svg class="w-5 h-5 text-gray-400 group-hover:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                                    </svg>
                                    <span class="text-sm font-medium text-gray-600 group-hover:text-blue-600">Create New Location</span>
                                </div>
                            </button>
                        </div>
                    {:else}
                        <!-- New Location Form -->
                        <div class="max-w-md mx-auto">
                            <div class="space-y-4">
                                <div>
                                    <label for="locationName" class="block text-sm font-medium text-gray-700 mb-2">
                                        Location Name
                                    </label>
                                    <input
                                        id="locationName"
                                        type="text"
                                        bind:value={locationName}
                                        placeholder="e.g., Factory Floor A, Warehouse Entrance..."
                                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                                    />
                                </div>
                                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                    <div class="flex">
                                        <svg class="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <div class="ml-3">
                                            <p class="text-sm text-blue-800">
                                                Choose a name that helps you easily identify this location in your dashboard.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {/if}
                </div>
            {:else if currentStep === 2}
                <!-- Step 2: Zone Setup -->
                <div class="flex-1 overflow-y-auto px-6 py-6">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <!-- Left: Zone Drawing Area -->
                        <div class="lg:col-span-2">
                            <div class="border border-gray-300 rounded-lg overflow-hidden bg-gray-50">
                                {#if customSnapshotPath}
                                    <ZoneDrawer
                                        onFinishZone={handleFinishZone}
                                        width={1200}
                                        height={675}
                                        bind:zones={zones}
                                        imageSrc={customSnapshotPath}
                                    />
                                {:else}
                                    <div class="flex items-center justify-center h-96 text-center">
                                        <div>
                                            <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                            </svg>
                                            <h3 class="text-lg font-medium text-gray-900 mb-2">No Snapshot Available</h3>
                                            <p class="text-sm text-gray-600">Fetch a snapshot from the camera to define monitoring zones.</p>
                                        </div>
                                    </div>
                                {/if}
                            </div>
                        </div>

                        <!-- Right: Controls and Zone List -->
                        <div class="space-y-4">
                            <!-- Fetch Snapshot Button -->
                            <div>
                                <h4 class="text-sm font-semibold text-gray-900 mb-2">Camera Snapshot</h4>
                                <button
                                    on:click={loadSnapshot}
                                    disabled={snapshotLoading || !locationName.trim()}
                                    class="w-full px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {#if snapshotLoading}
                                        <svg class="w-4 h-4 mr-2 inline animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                                        </svg>
                                        Fetching Snapshot...
                                    {:else}
                                        <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                        </svg>
                                        Fetch Snapshot
                                    {/if}
                                </button>
                                {#if snapshotError}
                                    <div class="mt-2 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800">
                                        {snapshotError}
                                    </div>
                                {/if}
                            </div>

                            <!-- Defined Zones -->
                            <div>
                                <h3 class="text-sm font-semibold text-gray-900 mb-2">Defined Zones</h3>
                                {#if zones.length > 0}
                                    <div class="space-y-2">
                                        {#each zones as zone, i}
                                            <div class="flex items-center gap-2 p-3 bg-white border border-gray-200 rounded-lg">
                                                <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                                                    {i + 1}
                                                </div>
                                                <div class="flex-1 min-w-0">
                                                    <div class="text-sm font-medium text-gray-900 truncate">{zone.name}</div>
                                                    <div class="text-xs text-gray-500">{zone.points.length} points</div>
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                {:else}
                                    <p class="text-sm text-gray-500">No zones defined yet. Click on the snapshot to start drawing.</p>
                                {/if}
                            </div>

                            <!-- Instructions -->
                            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h4 class="text-sm font-semibold text-blue-900 mb-2">Drawing Instructions</h4>
                                <ul class="text-xs text-blue-800 space-y-1">
                                    <li>• Click on the snapshot to place zone boundary points</li>
                                    <li>• Close the polygon to complete the zone</li>
                                    <li>• Enter a name for each zone</li>
                                    <li>• Add multiple zones as needed</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            {:else if currentStep === 3}
                <!-- Step 3: Summary -->
                <div class="flex-1 flex overflow-hidden">
                    <!-- Left Panel: Summary Information -->
                    <div class="w-72 border-r border-gray-200 bg-white p-4 overflow-y-auto flex-shrink-0">
                        <h3 class="text-lg font-bold text-gray-900 mb-4">Configuration Summary</h3>

                        <div class="space-y-4">
                            <!-- Location Info -->
                            <div>
                                <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1.5 flex items-center">
                                    <svg class="w-3.5 h-3.5 text-gray-400 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    </svg>
                                    Location
                                </h4>
                                <p class="text-sm font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded p-2.5">{locationName}</p>
                            </div>

                            <!-- Zones Info -->
                            <div>
                                <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1.5 flex items-center">
                                    <svg class="w-3.5 h-3.5 text-gray-400 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 9m0 8V9m0 0H9"></path>
                                    </svg>
                                    Monitoring Zones
                                </h4>

                                {#if zones.length > 0}
                                    <div class="space-y-1.5">
                                        {#each zones as zone, i}
                                            <div class="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200">
                                                <div class="w-6 h-6 bg-blue-600 text-white rounded flex items-center justify-center text-xs font-bold flex-shrink-0">
                                                    {i + 1}
                                                </div>
                                                <span class="text-xs font-medium text-gray-900 flex-1 truncate">{zone.name}</span>
                                                <span class="text-xs text-gray-500">{zone.points.length}pts</span>
                                            </div>
                                        {/each}
                                    </div>
                                {:else}
                                    <div class="p-2.5 bg-gray-50 border border-gray-200 rounded">
                                        <p class="text-xs text-gray-600">No zones - monitoring entire area</p>
                                    </div>
                                {/if}
                            </div>

                            <!-- Ready to Start -->
                            <div class="bg-green-50 border border-green-200 rounded p-3">
                                <div class="flex items-start gap-2">
                                    <svg class="w-5 h-5 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                    <div>
                                        <h5 class="text-xs font-bold text-green-900 mb-1">Ready to Start</h5>
                                        <p class="text-xs text-green-800">Click "Start Monitoring" to activate.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Panel: Visual Preview -->
                    <div class="flex-1 p-4 flex items-center justify-center bg-gray-100 overflow-auto">
                        {#if customSnapshotPath}
                            <div class="w-full max-w-7xl">
                                <ZoneDrawer
                                    onFinishZone={() => {}}
                                    width={1920}
                                    height={1080}
                                    zones={zones}
                                    readOnly={true}
                                    imageSrc={customSnapshotPath}
                                />
                            </div>
                        {:else}
                            <div class="text-center">
                                <svg class="w-20 h-20 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                </svg>
                                <p class="text-sm text-gray-500">No snapshot available</p>
                            </div>
                        {/if}
                    </div>
                </div>
            {/if}
        </div>

        <!-- Footer with Navigation -->
        {#if (showNewLocationForm || isEditingExisting) && viewMode === "edit"}
            <div class="border-t border-gray-200 px-6 py-4 bg-gray-50 flex-shrink-0">
                <div class="flex items-center justify-between">
                    <button
                        on:click={prevStep}
                        disabled={currentStep === 1}
                        class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                        </svg>
                        Previous
                    </button>

                    <div class="flex items-center space-x-2">
                        {#if currentStep < 3}
                            <button
                                on:click={nextStep}
                                disabled={currentStep === 1 && !canProceedStep1 || currentStep === 2 && !canProceedStep2}
                                class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Next
                                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                </svg>
                            </button>
                        {:else}
                            <button
                                on:click={handleStart}
                                class="inline-flex items-center px-6 py-2 text-sm font-medium rounded-md bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 transition-colors"
                            >
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293H15M9 10v4a2 2 0 002 2h2a2 2 0 002-2v-4M9 10V9a2 2 0 00-2-2h-2a2 2 0 00-2 2v1"></path>
                                </svg>
                                Start Monitoring
                            </button>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}
    </div>
</Modal>
