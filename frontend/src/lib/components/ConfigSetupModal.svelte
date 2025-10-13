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

    // Snapshot state
    let snapshotLoading = false;
    let snapshotError: string | null = null;
    let customSnapshotPath: string = '';

    // Load stored configuration when modal opens
    $: if (open) {
        loadStoredConfig();
        loadAllLocations();
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
            isEditingExisting = true;
            currentStep = 2;
        }
    }

    function loadExistingConfig() {
        if (storedConfig) {
            selectedLocationId = storedConfig.locationId;
            locationName = storedConfig.locationName;
            zones = [...storedConfig.zones];
            customSnapshotPath = storedConfig.snapshotPath || '';
            isEditingExisting = true;
            currentStep = 2;
        }
    }

    function startNewLocation() {
        showNewLocationForm = true;
        selectedLocationId = null;
        locationName = "";
        zones = [];
        customSnapshotPath = "";
        isEditingExisting = false;
    }

    async function removeStoredConfig() {
        const success = await deleteCurrentConfig();
        if (success) {
            storedConfig = null;
            await loadAllLocations();
        }
    }

    async function removeSelectedLocation(locationId: number) {
        if (confirm("Are you sure you want to delete this location and all its zones?")) {
            const success = await deleteLocationConfig(locationId);
            if (success) {
                await loadAllLocations();
                if (storedConfig && storedConfig.locationId === locationId) {
                    storedConfig = null;
                }
                if (selectedLocationId === locationId) {
                    selectedLocationId = null;
                    locationName = "";
                    zones = [];
                    customSnapshotPath = "";
                }
            }
        }
    }

    async function fetchSnapshot() {
        if (!locationName.trim()) {
            snapshotError = "Please enter a location name first";
            return;
        }

        snapshotLoading = true;
        snapshotError = null;

        try {
            const response = await fetch("http://10.10.67.44:8000/snapshot");
            if (!response.ok) {
                throw new Error(`Error fetching snapshot: ${response.statusText}`);
            }

            const blob = await response.blob();
            const blobURL = URL.createObjectURL(blob);
            customSnapshotPath = blobURL;

            console.log(`Snapshot fetched for location: ${locationName}`);

        } catch (err: any) {
            snapshotError = err.message;
            console.error('Error fetching snapshot:', err);
        } finally {
            snapshotLoading = false;
        }
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
            }
        }
    }

    function goToStep(step: number) {
        currentStep = step;
        if (step === 1) {
            isEditingExisting = false;
            showNewLocationForm = false;
        }
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

                const startResponse = await fetch("http://10.10.67.44:8000/system/start");
                const startResult = await startResponse.json();
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
        {#if showNewLocationForm || isEditingExisting}
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
        <div class="flex-1 overflow-auto">
            {#if currentStep === 1}
                <!-- Step 1: Location Selection -->
                <div class="px-6 py-8">
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
                                                    Edit Configuration
                                                </button>
                                                <button
                                                    on:click={removeStoredConfig}
                                                    class="px-3 py-1.5 text-xs font-medium rounded-md border border-red-300 bg-white text-red-700 hover:bg-red-50 transition-colors"
                                                >
                                                    Deactivate
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
                <div class="px-6 py-6">
                    <!-- Snapshot Controls -->
                    <div class="mb-6 bg-white border border-gray-200 rounded-lg p-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <h4 class="text-sm font-semibold text-gray-900 mb-1">Camera Snapshot</h4>
                                <p class="text-xs text-gray-500">Fetch a live snapshot from the camera to draw zones on</p>
                            </div>
                            <button
                                on:click={fetchSnapshot}
                                disabled={snapshotLoading || !locationName.trim()}
                                class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {#if snapshotLoading}
                                    <svg class="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                                    </svg>
                                    Fetching...
                                {:else}
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    </svg>
                                    Fetch Snapshot
                                {/if}
                            </button>
                            <!-- Error message -->
                            {#if snapshotError}
                                <div class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                                    <div class="flex">
                                        <svg class="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <div class="ml-2">
                                            <p class="text-sm text-red-800">{snapshotError}</p>
                                        </div>
                                    </div>
                                </div>
                            {/if}

                            <!-- Success message -->
                            {#if customSnapshotPath && customSnapshotPath !== ''}
                                <div class="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                                    <div class="flex">
                                        <svg class="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        <div class="ml-2">
                                            <p class="text-sm text-green-800">Snapshot fetched successfully! You can now draw zones on the live camera feed.</p>
                                        </div>
                                    </div>
                                </div>
                            {/if}
                        </div>

                        <!-- Zone Drawer -->
                        {#if customSnapshotPath}
                            <ZoneDrawer
                                onFinishZone={handleFinishZone}
                                width={1200}
                                height={675}
                                bind:zones={zones}
                                imageSrc={customSnapshotPath}
                            />
                        {:else}
                            <div class="border border-gray-200 rounded-lg p-12 bg-gray-50 text-center">
                                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                </svg>
                                <h3 class="text-lg font-medium text-gray-900 mb-2">No Snapshot Available</h3>
                                <p class="text-sm text-gray-600 mb-4">Please fetch a snapshot from the camera to define monitoring zones.</p>
                            </div>
                        {/if}
                    </div>
                </div>
            {:else if currentStep === 3}
                <!-- Step 3: Summary -->
                <div class="px-6 py-8">
                    <div class="max-w-2xl mx-auto">
                        <div class="space-y-6">
                            <!-- Location Summary -->
                            <div class="bg-white border border-gray-200 rounded-lg p-6">
                                <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                                    <svg class="w-4 h-4 text-gray-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    </svg>
                                    Location
                                </h4>
                                <p class="text-gray-700 font-medium">{locationName}</p>
                            </div>

                            <!-- Zones Summary -->
                            <div class="bg-white border border-gray-200 rounded-lg p-6">
                                <h4 class="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                                    <svg class="w-4 h-4 text-gray-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 9m0 8V9m0 0H9"></path>
                                    </svg>
                                    Monitoring Zones ({zones.length})
                                </h4>

                                {#if zones.length > 0}
                                    <div class="space-y-2 mb-4 max-h-32 overflow-y-auto">
                                        {#each zones as zone, i}
                                            <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                                                <span class="text-sm font-medium text-gray-700">{zone.name}</span>
                                                <span class="text-xs text-gray-500">{zone.points.length} points</span>
                                            </div>
                                        {/each}
                                    </div>
                                {:else}
                                    <div class="mb-4 p-3 bg-gray-50 rounded-lg">
                                        <p class="text-sm text-gray-600">No zones defined - monitoring will cover the entire area</p>
                                    </div>
                                {/if}

                                <!-- Zone Preview - Always show image with zones overlaid -->
                                {#if customSnapshotPath}
                                    <div class="border border-gray-200 rounded-lg overflow-hidden">
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
                                    <div class="border border-gray-200 rounded-lg p-6 bg-gray-50">
                                        <p class="text-sm text-gray-600 text-center">No snapshot available for preview</p>
                                    </div>
                                {/if}
                            </div>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Footer with Navigation -->
        {#if showNewLocationForm || isEditingExisting}
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
