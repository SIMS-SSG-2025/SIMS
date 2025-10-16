<script lang="ts">
	import { onMount } from 'svelte';
	import {
		fetchEventsForLocation,
		calculateStatsFromEvents,
		calculatePPEComplianceFromEvents,
		createBarChartDataFromEvents,
		calculateTimeRange,
		type DashboardStats,
		type PPEComplianceData,
		type DetectionBarChartData,
		type TimeRangeOption,
		type TimeRange
	} from '$lib/api/stats';
	import StatCard from '$lib/components/StatCard.svelte';
	import BarChart from '$lib/components/BarChart.svelte';
	import PieChart from '$lib/components/PieChart.svelte';

	// Props (you can pass these from parent component)
	export let locationId = 1;

	// State
	let timeRangeOption: TimeRangeOption = 'day';
	let customTimeRange: TimeRange | null = null;
	let stats: DashboardStats | null = null;
	let ppeCompliance: PPEComplianceData | null = null;
	let barChartData: DetectionBarChartData | null = null;
	let loading = false;
	let error = '';
	let lastUpdated: Date | null = null;

	// Refresh interval (in milliseconds)
	const REFRESH_INTERVAL = 30000; // 30 seconds
	let refreshTimer: NodeJS.Timeout;

	async function loadData() {
		loading = true;
		error = '';

		try {
			// Calculate time range
			const timeRange = customTimeRange || calculateTimeRange(timeRangeOption);

			// Fetch events from API
			const response = await fetchEventsForLocation(locationId, timeRange);

			// Transform data
			stats = calculateStatsFromEvents(response.events);
			ppeCompliance = calculatePPEComplianceFromEvents(response.events);
			barChartData = createBarChartDataFromEvents(response.events, timeRange);

			lastUpdated = new Date();
			console.log(`Loaded ${response.count} events for location ${locationId}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load events data';
			console.error('Error loading events:', err);
		} finally {
			loading = false;
		}
	}

	function handleTimeRangeChange(option: TimeRangeOption) {
		timeRangeOption = option;
		customTimeRange = null; // Clear custom range when using preset
		loadData();
	}

	function handleCustomTimeRange(range: TimeRange) {
		customTimeRange = range;
		timeRangeOption = 'custom';
		loadData();
	}

	function setupAutoRefresh() {
		clearInterval(refreshTimer);
		refreshTimer = setInterval(() => {
			loadData();
		}, REFRESH_INTERVAL);
	}

	onMount(() => {
		loadData();
		setupAutoRefresh();

		// Cleanup
		return () => {
			clearInterval(refreshTimer);
		};
	});

	// Format last updated time
	$: lastUpdatedText = lastUpdated
		? lastUpdated.toLocaleTimeString()
		: 'Never';
</script>

<div class="events-dashboard">
	<div class="dashboard-header">
		<h1>Location {locationId} - Events Dashboard</h1>
		<div class="header-actions">
			{#if lastUpdated}
				<span class="last-updated">Last updated: {lastUpdatedText}</span>
			{/if}
			<button class="refresh-btn" on:click={loadData} disabled={loading}>
				{loading ? 'Refreshing...' : 'Refresh'}
			</button>
		</div>
	</div>

	<!-- Time Range Selector -->
	<div class="time-range-selector">
		<button
			class:active={timeRangeOption === 'day'}
			on:click={() => handleTimeRangeChange('day')}
		>
			Today
		</button>
		<button
			class:active={timeRangeOption === 'week'}
			on:click={() => handleTimeRangeChange('week')}
		>
			Week
		</button>
		<button
			class:active={timeRangeOption === 'month'}
			on:click={() => handleTimeRangeChange('month')}
		>
			Month
		</button>
		<button
			class:active={timeRangeOption === 'all'}
			on:click={() => handleTimeRangeChange('all')}
		>
			All Time
		</button>
		<!-- You can add custom date picker here -->
	</div>

	<!-- Loading State -->
	{#if loading && !stats}
		<div class="loading-state">
			<p>Loading events data...</p>
		</div>
	{/if}

	<!-- Error State -->
	{#if error}
		<div class="error-state">
			<p class="error-message">{error}</p>
			<button on:click={loadData}>Retry</button>
		</div>
	{/if}

	<!-- Dashboard Content -->
	{#if stats && !error}
		<!-- Statistics Cards -->
		<div class="stats-grid">
			<StatCard
				title="Detected Persons"
				value={stats.detectedPersons}
				icon="users"
				iconColor="text-blue-600"
			/>
			<StatCard
				title="Detected Vehicles"
				value={stats.detectedVehicles}
				icon="truck"
				iconColor="text-green-600"
			/>
			<StatCard
				title="PPE Breaches"
				value={stats.ppeBreaches}
				icon="alert-triangle"
				iconColor="text-orange-600"
			/>
			<StatCard
				title="Zone Entries"
				value={stats.forbiddenZoneEntries}
				icon="map-pin"
				iconColor="text-red-600"
			/>
		</div>

		<!-- Charts Section -->
		<div class="charts-grid">
			<!-- Bar Chart -->
			{#if barChartData}
				<div class="chart-container">
					<h2>Detections Over Time</h2>
					<BarChart
						labels={barChartData.labels}
						datasets={[
							{
								label: 'Persons',
								data: barChartData.persons,
								backgroundColor: 'rgba(59, 130, 246, 0.7)'
							},
							{
								label: 'Vehicles',
								data: barChartData.vehicles,
								backgroundColor: 'rgba(34, 197, 94, 0.7)'
							}
						]}
					/>
				</div>
			{/if}

			<!-- PPE Compliance Pie Chart -->
			{#if ppeCompliance}
				<div class="chart-container">
					<h2>PPE Compliance</h2>
					<PieChart
						labels={['Compliant', 'Missing Hard Hat', 'Missing Vest', 'Missing Both']}
						data={[
							ppeCompliance.compliant,
							ppeCompliance.missingHardHat,
							ppeCompliance.missingVest,
							ppeCompliance.missingBoth
						]}
						backgroundColor={['#22c55e', '#f59e0b', '#ef4444', '#dc2626']}
					/>

					<!-- Compliance Summary -->
					<div class="compliance-summary">
						<div class="compliance-stat">
							<span class="label">Total Events:</span>
							<span class="value">
								{ppeCompliance.compliant + ppeCompliance.missingHardHat +
								 ppeCompliance.missingVest + ppeCompliance.missingBoth}
							</span>
						</div>
						<div class="compliance-stat">
							<span class="label">Compliance Rate:</span>
							<span class="value compliance-rate">
								{((ppeCompliance.compliant /
								  (ppeCompliance.compliant + ppeCompliance.missingHardHat +
								   ppeCompliance.missingVest + ppeCompliance.missingBoth)) * 100
								).toFixed(1)}%
							</span>
						</div>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.events-dashboard {
		padding: 2rem;
		max-width: 1400px;
		margin: 0 auto;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	.dashboard-header h1 {
		font-size: 1.875rem;
		font-weight: 700;
		color: #1f2937;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.last-updated {
		font-size: 0.875rem;
		color: #6b7280;
	}

	.refresh-btn {
		padding: 0.5rem 1rem;
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 0.375rem;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.2s;
	}

	.refresh-btn:hover:not(:disabled) {
		background: #2563eb;
	}

	.refresh-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.time-range-selector {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 2rem;
		padding: 0.5rem;
		background: #f3f4f6;
		border-radius: 0.5rem;
	}

	.time-range-selector button {
		padding: 0.5rem 1rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
		cursor: pointer;
		font-weight: 500;
		color: #374151;
		transition: all 0.2s;
	}

	.time-range-selector button:hover {
		background: #f9fafb;
	}

	.time-range-selector button.active {
		background: #3b82f6;
		color: white;
		border-color: #3b82f6;
	}

	.loading-state,
	.error-state {
		padding: 3rem;
		text-align: center;
	}

	.error-message {
		color: #dc2626;
		margin-bottom: 1rem;
		padding: 1rem;
		background: #fee2e2;
		border-radius: 0.5rem;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.charts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
		gap: 2rem;
	}

	.chart-container {
		background: white;
		padding: 1.5rem;
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.chart-container h2 {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.compliance-summary {
		margin-top: 1.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e5e7eb;
	}

	.compliance-stat {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
	}

	.compliance-stat .label {
		color: #6b7280;
		font-weight: 500;
	}

	.compliance-stat .value {
		font-weight: 600;
		color: #1f2937;
	}

	.compliance-rate {
		color: #22c55e;
		font-size: 1.125rem;
	}

	@media (max-width: 768px) {
		.events-dashboard {
			padding: 1rem;
		}

		.dashboard-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 1rem;
		}

		.charts-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
