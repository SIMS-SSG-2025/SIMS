<script lang="ts">
    import Modal from "./modal.svelte";
    import ZoneDrawer from "./ZoneDrawer.svelte";
    import { Check, ChevronRight, Camera, LoaderCircle, MapPin, Eye, Trash2, Plus, ArrowLeft, Save, X, SquarePen, Image, Info, Map, CircleStop } from 'lucide-svelte';
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
        getSystemStatus,
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
    let tempZoneNames: Record<number, string> = {}; // Temporary storage for zone names being edited
    let zoneNameInputs: Record<number, HTMLInputElement> = {}; // References to zone name input elements

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
    let startingSystem = false;
    let systemStatusMessage: string = '';
    let locationsLoading = false;

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
        locationsLoading = true;
        allLocations = await fetchAllLocations();
        locationsLoading = false;
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
        currentStep = 3; // Go to zones step
    }

    async function makeLocationActive(locationId: number) {
        try {
            startingSystem = true;
            systemStatusMessage = '';

            // Check if system is currently running
            const isRunning = await getSystemStatus();

            if (isRunning) {
                // Stop the system first
                systemStatusMessage = 'Stopping current monitoring...';
                await stopSystem();
                console.log("System stopped, waiting for device polling cycle...");

                // Wait 5 seconds for device to detect the stop
                systemStatusMessage = 'Waiting for system to stop...';
                await new Promise(resolve => setTimeout(resolve, 5000));
            }

            // Activate the new location configuration
            systemStatusMessage = 'Activating location...';
            const success = await activateLocation(locationId);

            if (success) {
                // Start the system with the new config
                systemStatusMessage = 'Starting monitoring...';
                await startSystem();
                await loadStoredConfig();
                await loadAllLocations();

                console.log("Location activated and system started");
                systemStatusMessage = '';

                // Return to list view to show the new active location
                viewMode = "list";
            } else {
                systemStatusMessage = '';
                alert("Failed to activate location");
            }
        } catch (error: any) {
            console.error("Error activating location:", error);
            systemStatusMessage = '';
            alert(`Error: ${error.message}`);
        } finally {
            startingSystem = false;
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
        if (confirm("⚠️ WARNING: This will permanently delete this location, all its zones, and ALL associated data (events, object positions, etc.).\n\nThis action cannot be undone. Are you sure you want to continue?")) {
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

    async function handleStopSystem() {
        if (confirm("Stop the monitoring system? You can restart it later from any location.")) {
            try {
                startingSystem = true;
                systemStatusMessage = 'Stopping monitoring system...';
                await stopSystem();

                // Wait a moment for the backend to deactivate the location
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Reload both stored config and all locations from backend
                // The backend has deactivated the location, so storedConfig should be null
                await loadStoredConfig();
                await loadAllLocations();

                systemStatusMessage = '';
                backToList();
            } catch (error: any) {
                console.error("Error stopping system:", error);
                systemStatusMessage = '';
                alert(`Error stopping system: ${error.message}`);
            } finally {
                startingSystem = false;
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
        { id: 1, title: "Setup", description: "Choose or create location" },
        { id: 2, title: "Snapshot", description: "Capture camera view" },
        { id: 3, title: "Zones", description: "Define monitoring zones" },
        { id: 4, title: "Summary", description: "Review configuration" }
    ];

    function nextStep() {
        if (currentStep < 4) {
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
        // Focus on the name input for the newly added zone
        // Use setTimeout to ensure DOM has updated
        setTimeout(() => {
            const newZoneIndex = zones.length - 1;
            if (zoneNameInputs[newZoneIndex]) {
                zoneNameInputs[newZoneIndex].focus();
            }
        }, 0);
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
            startingSystem = true;
            systemStatusMessage = '';

            // Check if system is currently running
            const isRunning = await getSystemStatus();

            if (isRunning) {
                // Stop the system first
                systemStatusMessage = 'Stopping current monitoring...';
                await stopSystem();
                console.log("System stopped, waiting for device polling cycle...");

                // Wait 5 seconds for device to detect the stop
                systemStatusMessage = 'Waiting for system to stop...';
                await new Promise(resolve => setTimeout(resolve, 5000));
            }

            // Save the new configuration
            systemStatusMessage = 'Saving configuration...';
            const success = await saveConfig(locationName, zones);

            if (success) {
                console.log("Configuration saved successfully");

                // Start the system with new config
                systemStatusMessage = 'Starting monitoring with new configuration...';
                let startResult = await startSystem();
                console.log("System start response:", startResult);

                systemStatusMessage = 'Monitoring started successfully!';

                // Brief delay to show success message
                await new Promise(resolve => setTimeout(resolve, 1000));

                handleClose();
            } else {
                systemStatusMessage = '';
                alert("Failed to setup configuration");
            }
        } catch (error: any) {
            console.error("Error setting up configuration:", error);
            systemStatusMessage = '';
            alert(`Error: ${error.message}`);
        } finally {
            startingSystem = false;
        }
    }

    $: canProceedStep1 = locationName.trim().length > 0;
    $: canProceedStep2 = customSnapshotPath.trim().length > 0;
    $: canProceedStep3 = zones.length === 0 || zones.every(zone => zone.name && zone.name.trim().length > 0); // All zones must have names
    $: unnamedZonesCount = zones.filter(zone => !zone.name || zone.name.trim().length === 0).length;
    $: modalWidth = currentStep === 3 ? 'max-w-7xl' : 'max-w-4xl'; // Larger width for zone drawing step

</script>

<Modal {open} onClose={handleClose} modalClass="p-0 w-full {modalWidth} max-h-[90vh] flex flex-col">
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
                            class="flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-colors flex-shrink-0
                                {currentStep === step.id
                                    ? 'bg-[#E76A23] text-white'
                                    : currentStep > step.id
                                        ? 'bg-green-500 text-white'
                                        : 'bg-gray-200 text-gray-600'}"
                            on:click={() => goToStep(step.id)}
                            disabled={step.id > 1 && !canProceedStep1 || step.id > 2 && !canProceedStep2 || step.id > 3 && !canProceedStep3}
                        >
                            {#if currentStep > step.id}
                                <Check class="w-4 h-4" />
                            {:else}
                                {step.id}
                            {/if}
                        </button>
                        <div class="ml-3">
                            <p class="text-sm font-medium text-gray-900">{step.title}</p>
                            <p class="text-xs text-gray-500">{step.description}</p>
                        </div>
                        {#if index < steps.length - 1}
                            <div class="w-12 h-px bg-gray-300 mx-4 flex-shrink-0"></div>
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

                        <!-- Loading State -->
                        {#if locationsLoading}
                            <div class="flex items-center justify-center py-12">
                                <div class="text-center">
                                    <LoaderCircle class="w-8 h-8 text-[#E76A23] animate-spin mx-auto mb-3" />
                                    <p class="text-sm text-gray-600">Loading configurations...</p>
                                </div>
                            </div>
                        {:else}
                            <!-- Current Active Location -->
                            {#if storedConfig}
                                <button
                                    on:click={loadExistingConfig}
                                    class="w-full mb-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg hover:bg-green-100 transition-colors cursor-pointer text-left"
                                >
                                    <div class="flex items-start justify-between">
                                        <div class="flex-1">
                                            <div class="flex items-center gap-2 mb-2">
                                                <span class="px-2 py-1 bg-green-600 text-white text-xs font-semibold rounded">CURRENTLY RUNNING</span>
                                                <h4 class="text-base font-semibold text-gray-900">{storedConfig.locationName}</h4>
                                            </div>
                                            <p class="text-sm text-gray-600 mb-1">
                                                {storedConfig.zones.length} zone{storedConfig.zones.length !== 1 ? 's' : ''} configured
                                            </p>
                                            <p class="text-xs text-green-700 font-medium">Click to edit</p>
                                        </div>
                                    </div>
                                </button>
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
                                            <div class="relative group">
                                                <button
                                                    on:click={() => selectLocation(location.locationId)}
                                                    class="w-full flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-[#E76A23] hover:bg-orange-50 transition-colors cursor-pointer text-left"
                                                >
                                                    <div class="flex-1">
                                                        <h5 class="text-sm font-medium text-gray-900">{location.locationName}</h5>
                                                        <p class="text-xs text-gray-500">
                                                            {location.zoneCount} zone{location.zoneCount !== 1 ? 's' : ''}
                                                        </p>
                                                        <p class="text-xs text-[#E76A23] font-medium mt-1 opacity-0 group-hover:opacity-100 transition-opacity">Click to edit</p>
                                                    </div>
                                                </button>
                                                <div class="absolute right-4 top-1/2 -translate-y-1/2 flex gap-2 z-10">
                                                    <button
                                                        on:click|stopPropagation={() => makeLocationActive(location.locationId)}
                                                        class="px-3 py-1.5 text-xs font-medium rounded-md bg-green-600 text-white hover:bg-green-700 transition-colors"
                                                        title="Activate this location"
                                                    >
                                                        Activate
                                                    </button>
                                                    <button
                                                        on:click|stopPropagation={() => removeSelectedLocation(location.locationId)}
                                                        class="px-3 py-1.5 text-xs font-medium rounded-md bg-white border border-red-300 text-red-700 hover:bg-red-50 transition-colors"
                                                        title="Delete this location"
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
                                class="w-full py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-[#E76A23] hover:bg-orange-50 transition-colors group"
                            >
                                <div class="flex items-center justify-center gap-2">
                                    <Plus class="w-5 h-5 text-gray-400 group-hover:text-[#E76A23]" />
                                    <span class="text-sm font-medium text-gray-600 group-hover:text-[#E76A23]">Create New Configuration</span>
                                </div>
                            </button>
                        {/if}
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
                                <ArrowLeft class="w-4 h-4 inline mr-1" />
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
                                                <div class="w-7 h-7 bg-[#E76A23] text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
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
                                    disabled={startingSystem}
                                    class="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {#if startingSystem}
                                        <LoaderCircle class="w-5 h-5 animate-spin" />
                                        {systemStatusMessage || 'Activating...'}
                                    {:else}
                                        <Check class="w-5 h-5" />
                                        Set as Active
                                    {/if}
                                </button>
                            {/if}
                            <button
                                on:click={editLocation}
                                class="w-full px-4 py-3 bg-[#E76A23] text-white rounded-lg hover:bg-[#d15e1e] transition font-medium shadow-sm flex items-center justify-center gap-2"
                            >
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                                </svg>
                                Edit
                            </button>
                            {#if storedConfig && selectedLocationId === storedConfig.locationId}
                                <!-- Stop button for active location -->
                                <button
                                    on:click={handleStopSystem}
                                    disabled={startingSystem}
                                    class="w-full px-4 py-3 border border-orange-700 bg-white text-orange-700 rounded-lg hover:bg-red-50 transition font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {#if startingSystem}
                                        <LoaderCircle class="w-5 h-5 animate-spin" />
                                        Stopping...
                                    {:else}
                                        <CircleStop class="w-5 h-5" />
                                        Stop Monitoring
                                    {/if}
                                </button>
                            {:else}
                                <!-- Delete button for non-active location -->
                                <button
                                    on:click={() => removeSelectedLocation(selectedLocationId!)}
                                    class="w-full px-4 py-3 border border-red-300 bg-white text-red-700 rounded-lg hover:bg-red-50 transition font-medium flex items-center justify-center gap-2"
                                >
                                    <Trash2 class="w-5 h-5" />
                                    Delete Location
                                </button>
                            {/if}
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
                                <Camera class="w-20 h-20 text-gray-300 mx-auto mb-4" />
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
                                <button
                                    on:click={loadExistingConfig}
                                    class="w-full mb-6 p-4 bg-orange-50 border-2 border-orange-200 rounded-lg hover:bg-orange-100 transition-colors cursor-pointer text-left"
                                >
                                    <div class="flex items-start justify-between">
                                        <div class="flex-1">
                                            <div class="flex items-center gap-2 mb-2">
                                                <span class="px-2 py-1 bg-[#E76A23] text-white text-xs font-semibold rounded">ACTIVE</span>
                                                <h4 class="text-base font-semibold text-gray-900">{storedConfig.locationName}</h4>
                                            </div>
                                            <p class="text-sm text-gray-600 mb-1">
                                                {storedConfig.zones.length} zone{storedConfig.zones.length !== 1 ? 's' : ''} configured
                                            </p>
                                            <p class="text-xs text-[#E76A23] font-medium">Click to edit</p>
                                        </div>
                                    </div>
                                </button>
                            {/if}

                            <!-- All Locations List -->
                            {#if allLocations.length > 0}
                                <div class="mb-6">
                                    <h4 class="text-sm font-semibold text-gray-700 mb-3">Available Locations</h4>
                                    <div class="space-y-2 max-h-96 overflow-y-auto">
                                        {#each allLocations as location}
                                            {#if !storedConfig || storedConfig.locationId !== location.locationId}
                                                <div class="relative group">
                                                    <button
                                                        on:click={() => selectLocation(location.locationId)}
                                                        class="w-full flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-[#E76A23] hover:bg-orange-50 transition-colors cursor-pointer text-left"
                                                    >
                                                        <div class="flex-1">
                                                            <h5 class="text-sm font-medium text-gray-900">{location.locationName}</h5>
                                                            <p class="text-xs text-gray-500">
                                                                {location.zoneCount} zone{location.zoneCount !== 1 ? 's' : ''}
                                                            </p>
                                                            <p class="text-xs text-[#E76A23] font-medium mt-1 opacity-0 group-hover:opacity-100 transition-opacity">Click to edit</p>
                                                        </div>
                                                    </button>
                                                    <div class="absolute right-4 top-1/2 -translate-y-1/2 flex gap-2 z-10">
                                                        <button
                                                            on:click|stopPropagation={() => removeSelectedLocation(location.locationId)}
                                                            class="px-3 py-1.5 text-xs font-medium rounded-md bg-white border border-red-300 text-red-700 hover:bg-red-50 transition-colors"
                                                            title="Delete this location"
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
                                class="w-full py-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-[#E76A23] hover:bg-orange-50 transition-colors group"
                            >
                                <div class="flex items-center justify-center gap-2">
                                    <Plus class="w-5 h-5 text-gray-400 group-hover:text-[#E76A23]" />
                                    <span class="text-sm font-medium text-gray-600 group-hover:text-[#E76A23]">Create New Location</span>
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
                                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#E76A23] focus:border-transparent text-sm"
                                    />
                                </div>
                                <div class="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                    <div class="flex">
                                        <Info class="w-5 h-5 text-[#E76A23] flex-shrink-0 mt-0.5" />
                                        <div class="ml-3">
                                            <p class="text-sm text-gray-800">
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
                <!-- Step 2: Snapshot -->
                <div class="flex-1 overflow-y-auto px-6 py-6">
                    <div class="max-w-4xl mx-auto h-full flex flex-col">
                        {#if !customSnapshotPath}
                            <!-- Title only shown when no snapshot -->
                            <div class="text-center mb-6">
                                <h3 class="text-2xl font-bold text-gray-900 mb-2">Camera Snapshot</h3>
                                <p class="text-gray-600">Capture a snapshot from the camera to use for zone configuration</p>
                            </div>
                        {/if}

                        {#if customSnapshotPath}
                            <!-- Snapshot Preview -->
                            <div class="flex-1 flex flex-col">
                                <div class="rounded-lg overflow-hidden p-3 flex-1 flex flex-col">
                                    <div class="flex items-center justify-between mb-2">
                                        <div class="flex items-center gap-2">
                                            <Check class="w-5 h-5 text-green-600" />
                                            <span class="text-sm font-semibold text-green-900">Snapshot Captured Successfully</span>
                                        </div>
                                        <button
                                            on:click={loadSnapshot}
                                            disabled={snapshotLoading}
                                            class="px-4 py-1.5 text-xs font-medium rounded-md border-2 border-[#E76A23] text-[#E76A23] hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                        >
                                            {#if snapshotLoading}
                                                <LoaderCircle class="w-3 h-3 mr-1.5 inline animate-spin" />
                                                Retaking...
                                            {:else}
                                                <Camera class="w-3 h-3 mr-1.5 inline" />
                                                Retake
                                            {/if}
                                        </button>
                                    </div>
                                    <div class="border border-gray-300 rounded-lg overflow-hidden bg-white flex-1">
                                        <img src={customSnapshotPath} alt="Camera Snapshot" class="w-full h-full object-contain" />
                                    </div>
                                </div>
                            </div>
                        {:else}
                            <!-- No Snapshot - Fetch Button -->
                            <div class="text-center">
                                <div class="mb-6">
                                    <Camera class="w-24 h-24 text-gray-300 mx-auto mb-4" />
                                </div>

                                <button
                                    on:click={loadSnapshot}
                                    disabled={snapshotLoading || !locationName.trim()}
                                    class="px-8 py-3 text-base font-medium rounded-md bg-[#E76A23] text-white hover:bg-[#d15e1e] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {#if snapshotLoading}
                                        <LoaderCircle class="w-5 h-5 mr-2 inline animate-spin" />
                                        Fetching Snapshot...
                                    {:else}
                                        <Camera class="w-5 h-5 mr-2 inline" />
                                        Fetch Snapshot
                                    {/if}
                                </button>

                                {#if !locationName.trim()}
                                    <p class="text-xs text-gray-500 mt-3">Enter a location name in Step 1 to fetch a snapshot</p>
                                {/if}
                            </div>
                        {/if}

                        {#if snapshotError}
                            <div class="mt-3 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800">
                                <strong>Error:</strong> {snapshotError}
                            </div>
                        {/if}

                        {#if !customSnapshotPath}
                            <!-- Instructions only shown when no snapshot -->
                            <div class="bg-orange-50 border border-orange-200 rounded-lg p-4 mt-6">
                                <div class="flex">
                                    <Info class="w-5 h-5 text-[#E76A23] flex-shrink-0 mt-0.5" />
                                    <div class="ml-3">
                                        <p class="text-sm text-gray-800">
                                            Make sure there are no people in the camera view when taking the snapshot.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>
            {:else if currentStep === 3}
                <!-- Step 3: Zone Setup -->
                <div class="flex-1 overflow-y-auto px-6 py-6">
                    <div class="flex gap-6 h-full">
                        <!-- Left: Zone Drawing Area (Much Larger) -->
                        <div class="flex-1">
                            <div class="border border-gray-300 rounded-lg overflow-hidden bg-gray-50 h-full">
                                {#if customSnapshotPath}
                                    <ZoneDrawer
                                        onFinishZone={handleFinishZone}
                                        width={1600}
                                        height={900}
                                        bind:zones={zones}
                                        imageSrc={customSnapshotPath}
                                        hideControls={true}
                                    />
                                {:else}
                                    <div class="flex items-center justify-center h-96 text-center">
                                        <div>
                                            <Camera class="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                            <h3 class="text-lg font-medium text-gray-900 mb-2">No Snapshot Available</h3>
                                            <p class="text-sm text-gray-600">Go back to Step 2 to fetch a snapshot.</p>
                                        </div>
                                    </div>
                                {/if}
                            </div>
                        </div>

                        <!-- Right: Zone List and Instructions -->
                        <div class="w-80 space-y-4 flex-shrink-0">
                            <!-- Defined Zones -->
                            <div>
                                <div class="flex items-center justify-between mb-2">
                                    <h3 class="text-sm font-semibold text-gray-900">Defined Zones ({zones.length})</h3>
                                    {#if unnamedZonesCount > 0}
                                        <span class="text-xs font-medium text-orange-600 bg-orange-100 px-2 py-1 rounded">
                                            {unnamedZonesCount} unnamed
                                        </span>
                                    {/if}
                                </div>
                                {#if zones.length > 0}
                                    <div class="space-y-2">
                                        {#each zones as zone, i}
                                            {#if zone.name}
                                                <!-- Named zone -->
                                                <div class="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
                                                    <div class="w-7 h-7 bg-[#E76A23] text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                                                        {i + 1}
                                                    </div>
                                                    <div class="flex-1 min-w-0">
                                                        <div class="text-sm font-medium text-gray-900 truncate">{zone.name}</div>
                                                        <div class="text-xs text-gray-500">{zone.points.length} points</div>
                                                    </div>
                                                    <button
                                                        on:click={() => {
                                                            zones = zones.filter((_, index) => index !== i);
                                                        }}
                                                        class="text-gray-400 hover:text-red-500 transition-colors p-1"
                                                        title="Delete zone"
                                                    >
                                                        <X class="w-4 h-4" />
                                                    </button>
                                                </div>
                                            {:else}
                                                <!-- Unnamed zone - needs name input -->
                                                <div class="p-3 bg-white border-2 border-gray-300 rounded-lg">
                                                    <div class="flex items-center gap-3 mb-2.5">
                                                        <div class="w-7 h-7 bg-gray-200 text-gray-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                                                            {i + 1}
                                                        </div>
                                                        <div class="flex-1 text-xs text-gray-500">
                                                            {zone.points.length} points
                                                        </div>
                                                        <button
                                                            on:click={() => {
                                                                zones = zones.filter((_, index) => index !== i);
                                                            }}
                                                            class="text-gray-400 hover:text-red-500 transition-colors p-1"
                                                            title="Delete zone"
                                                        >
                                                            <X class="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                    <div class="flex items-center gap-2">
                                                        <input
                                                            bind:this={zoneNameInputs[i]}
                                                            type="text"
                                                            value={tempZoneNames[i] !== undefined ? tempZoneNames[i] : zone.name}
                                                            on:input={(e) => {
                                                                tempZoneNames[i] = e.currentTarget.value;
                                                            }}
                                                            placeholder="Enter zone name..."
                                                            class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-[#E76A23] focus:border-transparent"
                                                            on:keydown={(e) => {
                                                                if (e.key === 'Enter') {
                                                                    const name = tempZoneNames[i] !== undefined ? tempZoneNames[i] : zone.name;
                                                                    if (name && name.trim()) {
                                                                        zone.name = name.trim();
                                                                        delete tempZoneNames[i];
                                                                        zones = [...zones]; // Trigger reactivity to update UI
                                                                    }
                                                                }
                                                            }}
                                                        />
                                                        <button
                                                            on:click={() => {
                                                                const name = tempZoneNames[i] !== undefined ? tempZoneNames[i] : zone.name;
                                                                if (name && name.trim()) {
                                                                    zone.name = name.trim();
                                                                    delete tempZoneNames[i];
                                                                    zones = [...zones]; // Trigger reactivity to update UI
                                                                }
                                                            }}
                                                            disabled={!tempZoneNames[i] && (!zone.name || !zone.name.trim()) || (tempZoneNames[i] !== undefined && !tempZoneNames[i].trim())}
                                                            class="px-4 py-2 text-sm font-medium rounded-md bg-[#E76A23] text-white hover:bg-[#d15e1e] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                                        >
                                                            Save
                                                        </button>
                                                    </div>
                                                </div>
                                            {/if}
                                        {/each}
                                    </div>
                                {:else}
                                    <p class="text-sm text-gray-500">No zones defined yet. Click on the snapshot to start drawing.</p>
                                {/if}
                            </div>

                            <!-- Instructions -->
                            <div class="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                <h4 class="text-sm font-semibold text-gray-900 mb-2">How to Draw Zones</h4>
                                <ul class="text-xs text-gray-800 space-y-1.5">
                                    <li>• <strong>Click</strong> to place boundary points (min 3)</li>
                                    <li>• Press <strong>Enter</strong> to finish zone</li>
                                    <li>• Enter zone name and click <strong>Save</strong></li>
                                    <li>• Press <strong>ESC</strong> to cancel current drawing</li>
                                    <li>• All zones must be named before continuing</li>
                                    <li>• Zones are optional - skip this step if needed</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            {:else if currentStep === 4}
                <!-- Step 4: Summary -->
                <div class="flex-1 flex overflow-hidden">
                    <!-- Left Panel: Summary Information -->
                    <div class="w-72 border-r border-gray-200 bg-white p-4 overflow-y-auto flex-shrink-0">
                        <h3 class="text-lg font-bold text-gray-900 mb-4">Configuration Summary</h3>

                        <div class="space-y-4">
                            <!-- Location Info -->
                            <div>
                                <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1.5 flex items-center">
                                    <MapPin class="w-3.5 h-3.5 text-gray-400 mr-1.5" />
                                    Location
                                </h4>
                                <p class="text-sm font-semibold text-gray-900 bg-gray-50 border border-gray-200 rounded p-2.5">{locationName}</p>
                            </div>

                            <!-- Zones Info -->
                            <div>
                                <h4 class="text-xs font-semibold text-gray-500 uppercase mb-1.5 flex items-center">
                                    <Map class="w-3.5 h-3.5 text-gray-400 mr-1.5" />
                                    Monitoring Zones
                                </h4>

                                {#if zones.length > 0}
                                    <div class="space-y-1.5">
                                        {#each zones as zone, i}
                                            <div class="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200">
                                                <div class="w-6 h-6 bg-[#E76A23] text-white rounded flex items-center justify-center text-xs font-bold flex-shrink-0">
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
                                    <Check class="w-5 h-5 text-green-600 flex-shrink-0" />
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
                        class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#E76A23] focus:ring-offset-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <ArrowLeft class="w-4 h-4 mr-2" />
                        Previous
                    </button>

                    <div class="flex items-center space-x-2">
                        {#if currentStep < 4}
                            <button
                                on:click={nextStep}
                                disabled={currentStep === 1 && !canProceedStep1 || currentStep === 2 && !canProceedStep2 || currentStep === 3 && !canProceedStep3}
                                class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-[#E76A23] text-white hover:bg-[#d15e1e] focus:outline-none focus:ring-2 focus:ring-[#E76A23] focus:ring-offset-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Next
                                <ChevronRight class="w-4 h-4 ml-2" />
                            </button>
                        {:else}
                            <button
                                on:click={handleStart}
                                disabled={startingSystem}
                                class="inline-flex items-center px-6 py-2 text-sm font-medium rounded-md bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {#if startingSystem}
                                    <LoaderCircle class="w-4 h-4 mr-2 animate-spin" />
                                    {systemStatusMessage || 'Starting...'}
                                {:else}
                                    <Save class="w-4 h-4 mr-2" />
                                    Start Monitoring
                                {/if}
                            </button>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}
    </div>
</Modal>
