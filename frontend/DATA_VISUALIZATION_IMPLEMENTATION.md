# Data Visualization Frontend Implementation

## Overview
This document describes the data visualization features added to the SIMS frontend dashboard. The implementation is API-ready with mock data structures in place for development.

## Features Implemented

### 1. Time Range Selection
- **Location**: Header center area
- **Options**:
  - Day (current day)
  - Week (last 7 days)
  - Month (last 30 days)
  - All (all time)
  - Custom (user-defined date range)
- **Visual Feedback**: Active selection highlighted in blue, custom range shows selected dates

### 2. Custom Date Range Picker
- **Component**: `DateRangePicker.svelte`
- **Features**:
  - Quick select buttons (7, 14, 30, 90 days)
  - Manual date selection with validation
  - Prevents future dates
  - Ensures start date is before end date
  - Clean modal interface

### 3. Statistics Cards
- **Component**: `StatCard.svelte`
- **Features**:
  - Displays counter value with icon
  - Shows trend indicator (up/down arrow with percentage)
  - Responsive design with hover effects
  - Color-coded icons

### 4. Dashboard Statistics
Four main counter cards:

1. **Detected Persons** (Blue)
   - Counts total person detections in selected time period
   - Icon: People/users icon

2. **Detected Vehicles** (Green)
   - Counts total vehicle detections in selected time period
   - Icon: Lightning bolt (representing vehicles)

3. **PPE Compliance Breaches** (Orange)
   - Counts PPE safety violations
   - Icon: Warning triangle
   - Trend direction inverted (decrease is positive)

4. **Forbidden Zone Entries** (Red)
   - Counts unauthorized zone entries
   - Icon: Prohibition symbol
   - Trend direction inverted (decrease is positive)

## API Integration Structure

### Data Types (`src/lib/api/stats.ts`)

```typescript
interface DashboardStats {
    detectedPersons: number;
    detectedVehicles: number;
    ppeBreaches: number;
    forbiddenZoneEntries: number;
    trends?: {
        detectedPersons?: number;
        detectedVehicles?: number;
        ppeBreaches?: number;
        forbiddenZoneEntries?: number;
    };
}

interface TimeRange {
    start: Date;
    end: Date;
}

type TimeRangeOption = 'day' | 'week' | 'month' | 'all' | 'custom';
```

### API Functions (Ready for Backend Integration)

The following functions are currently using mock data but are structured to easily swap in real API calls:

```typescript
// In stats.ts - Currently returns mock data
async function fetchStats(timeRange: TimeRange): Promise<DashboardStats>
async function fetchChartData(timeRange: TimeRange): Promise<ChartData>
```

**To integrate with backend**: Replace the mock return statements with actual fetch calls to your API endpoints.

Example:
```typescript
export async function fetchStats(timeRange: TimeRange): Promise<DashboardStats> {
    const response = await fetch(
        `http://your-api-url/api/stats?start=${timeRange.start.toISOString()}&end=${timeRange.end.toISOString()}`
    );
    return await response.json();
}
```

## Component Structure

### New Components
- `src/lib/components/StatCard.svelte` - Reusable statistics card
- `src/lib/components/DateRangePicker.svelte` - Custom date range selector

### New Utilities
- `src/lib/api/stats.ts` - Statistics data types and API functions

### Modified Components
- `src/routes/+page.svelte` - Main dashboard page with statistics integration

## State Management

The dashboard uses Svelte 5 runes for reactive state:
- `selectedRange` - Currently selected time range option
- `customTimeRange` - Start and end dates for custom range
- `stats` - Current statistics data
- `statsLoading` - Loading state for statistics

## Reactive Updates

Statistics automatically reload when:
1. User selects a different time range (Day/Week/Month/All)
2. User applies a custom date range
3. Component mounts initially

This is handled by the `$effect()` hook:
```typescript
$effect(() => {
    if (selectedRange) {
        loadStatistics();
    }
});
```

## Mock Data

For development purposes, mock data is generated with:
- Random values within realistic ranges
- Simulated trends (percentage changes)
- Time-series data generation for charts (prepared for future use)

## Next Steps for Backend Integration

1. **Create API endpoints** that match the expected data structure:
   - `GET /api/stats?start={iso_date}&end={iso_date}` → Returns `DashboardStats`
   - `GET /api/chart-data?start={iso_date}&end={iso_date}` → Returns `ChartData`

2. **Update the fetch functions** in `src/lib/api/stats.ts`:
   - Replace mock data returns with actual API calls
   - Add error handling
   - Add loading states if needed

3. **Configure API URL**:
   - Update the base URL in `src/lib/api/config.ts` or create environment variables
   - Ensure CORS is configured on the backend

## Design Decisions

1. **Trend Indicators**: For breach and entry counters, the trend logic is inverted (decrease = positive) since fewer violations is better.

2. **Date Formatting**: Uses ISO format (YYYY-MM-DD) for consistency with international standards.

3. **Mock Data**: Allows frontend development to proceed independently while backend endpoints are being developed.

4. **Reusable Components**: StatCard is designed to be reused elsewhere in the application if needed.

## Browser Compatibility

- Uses native date input (HTML5)
- Modern CSS (Grid, Flexbox)
- Svelte 5 runes syntax
- Requires modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
