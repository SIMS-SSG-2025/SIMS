import { API_BASE_URL } from './config';

// Types for dashboard statistics
export interface DashboardStats {
    detectedPersons: number;
    detectedVehicles: number;
    ppeBreaches: number;
    helmetBreaches: number;
    vestBreaches: number;
    riskZoneEntries: number;
    zoneEntryBreakdown: Map<number, number>; // zone_id -> count
}

export interface Event {
    event_id: number;
    object_id: number;
    zone_id: number;
    time: string;
    has_helmet: boolean;
    has_vest: boolean;
    location: string;
}

export interface EventsResponse {
    events: Event[];
    count: number;
}

export interface TimeRange {
    start: Date;
    end: Date;
}

export type TimeRangeOption = 'day' | 'week' | 'month' | 'all' | 'custom';

export interface ChartDataPoint {
    timestamp: string;
    value: number;
}

export interface ChartData {
    persons: ChartDataPoint[];
    vehicles: ChartDataPoint[];
    ppeBreaches: ChartDataPoint[];
    zoneEntries: ChartDataPoint[];
}

// Bar chart data for persons and vehicles over time
export interface DetectionBarChartData {
    labels: string[];
    persons: number[];
    vehicles: number[];
}

// PPE Compliance breakdown
export interface PPEComplianceData {
    compliant: number;
    missingHardHat: number;
    missingVest: number;
    missingBoth: number;
}

// Helper function to calculate time range based on option
export function calculateTimeRange(option: TimeRangeOption, customRange?: TimeRange, earliestEventTime?: Date): TimeRange {
    const now = new Date();
    let end = new Date();
    let start = new Date();

    switch (option) {
        case 'day':
            // Current day from 00:00:00 to 23:59:59
            start.setHours(0, 0, 0, 0);
            end.setHours(23, 59, 59, 999);
            break;
        case 'week':
            // Current week from Monday to Sunday
            const currentDay = now.getDay();
            const daysFromMonday = currentDay === 0 ? 6 : currentDay - 1; // If Sunday, go back 6 days, else go back to Monday
            const daysToSunday = currentDay === 0 ? 0 : 7 - currentDay; // Days until Sunday
            start = new Date(now);
            start.setDate(now.getDate() - daysFromMonday);
            start.setHours(0, 0, 0, 0);
            end = new Date(now);
            end.setDate(now.getDate() + daysToSunday);
            end.setHours(23, 59, 59, 999);
            break;
        case 'month':
            // Current month from 1st to last day
            start = new Date(now.getFullYear(), now.getMonth(), 1);
            start.setHours(0, 0, 0, 0);
            end = new Date(now.getFullYear(), now.getMonth() + 1, 0); // Last day of current month
            end.setHours(23, 59, 59, 999);
            break;
        case 'all':
            // Use earliest event time if provided, otherwise fallback to 2020
            if (earliestEventTime) {
                start = new Date(earliestEventTime);
                start.setHours(0, 0, 0, 0);
            } else {
                start = new Date(2020, 0, 1);
            }
            break;
        case 'custom':
            if (customRange) {
                return customRange;
            }
            break;
    }

    return { start, end };
}

/**
 * Find the earliest event timestamp from an array of events
 * @param events - Array of Event objects
 * @returns Date of earliest event, or null if no events
 */
export function findEarliestEventTime(events: Event[]): Date | null {
    if (events.length === 0) return null;

    const timestamps = events.map(event => new Date(event.time).getTime());
    const earliestTimestamp = Math.min(...timestamps);
    return new Date(earliestTimestamp);
}

// Mock data for development (to be replaced with API calls)
export function getMockStats(timeRange: TimeRange): DashboardStats {
    // This is placeholder data - will be replaced with actual API call
    const zoneEntryBreakdown = new Map<number, number>();
    // Mock some zone entries (zone IDs 1, 2, 3)
    zoneEntryBreakdown.set(1, Math.floor(Math.random() * 15) + 1);
    zoneEntryBreakdown.set(2, Math.floor(Math.random() * 10) + 1);
    const totalEntries = Array.from(zoneEntryBreakdown.values()).reduce((a, b) => a + b, 0);

    return {
        detectedPersons: Math.floor(Math.random() * 1000) + 100,
        detectedVehicles: Math.floor(Math.random() * 500) + 50,
        ppeBreaches: Math.floor(Math.random() * 50) + 5,
        helmetBreaches: Math.floor(Math.random() * 30) + 3,
        vestBreaches: Math.floor(Math.random() * 25) + 2,
        riskZoneEntries: totalEntries,
        zoneEntryBreakdown
    };
}

export function getMockDetectionBarChartData(timeRange: TimeRange): DetectionBarChartData {
    // Generate labels based on time range
    const labels: string[] = [];
    const persons: number[] = [];
    const vehicles: number[] = [];

    const hoursDiff = Math.floor((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60));
    let numPoints = 12; // Default number of bars

    // Adjust number of points based on time range
    if (hoursDiff <= 24) {
        // Day view - hourly data
        numPoints = 24;
        for (let i = 0; i < numPoints; i++) {
            labels.push(`${i}:00`);
            persons.push(Math.floor(Math.random() * 50) + 10);
            vehicles.push(Math.floor(Math.random() * 30) + 5);
        }
    } else if (hoursDiff <= 168) {
        // Week view - daily data
        numPoints = 7;
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const startDate = new Date(timeRange.start);
        for (let i = 0; i < numPoints; i++) {
            const date = new Date(startDate);
            date.setDate(date.getDate() + i);
            labels.push(days[date.getDay()]);
            persons.push(Math.floor(Math.random() * 200) + 50);
            vehicles.push(Math.floor(Math.random() * 100) + 20);
        }
    } else if (hoursDiff <= 720) {
        // Month view - daily data
        numPoints = 30;
        const startDate = new Date(timeRange.start);
        for (let i = 0; i < numPoints; i++) {
            const date = new Date(startDate);
            date.setDate(date.getDate() + i);
            labels.push(`${date.getMonth() + 1}/${date.getDate()}`);
            persons.push(Math.floor(Math.random() * 200) + 50);
            vehicles.push(Math.floor(Math.random() * 100) + 20);
        }
    } else {
        // All time - weekly data
        numPoints = 12;
        for (let i = 0; i < numPoints; i++) {
            labels.push(`Week ${i + 1}`);
            persons.push(Math.floor(Math.random() * 500) + 100);
            vehicles.push(Math.floor(Math.random() * 300) + 50);
        }
    }

    return { labels, persons, vehicles };
}

export function getMockPPEComplianceData(): PPEComplianceData {
    // Generate random PPE compliance data
    const total = 100;
    const compliant = Math.floor(Math.random() * 40) + 50; // 50-90% compliant
    const remaining = total - compliant;
    const missingHardHat = Math.floor(Math.random() * remaining * 0.4);
    const missingVest = Math.floor(Math.random() * (remaining - missingHardHat) * 0.6);
    const missingBoth = remaining - missingHardHat - missingVest;

    return {
        compliant,
        missingHardHat,
        missingVest,
        missingBoth
    };
}

export function getMockChartData(timeRange: TimeRange): ChartData {
    // Generate mock time series data
    const points: ChartDataPoint[] = [];
    const hoursDiff = Math.floor((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60));
    const numPoints = Math.min(hoursDiff, 24); // Max 24 points

    for (let i = 0; i < numPoints; i++) {
        const timestamp = new Date(timeRange.start.getTime() + (i * hoursDiff / numPoints * 60 * 60 * 1000));
        points.push({
            timestamp: timestamp.toISOString(),
            value: Math.floor(Math.random() * 50)
        });
    }

    return {
        persons: points.map(p => ({ ...p, value: Math.floor(Math.random() * 50) })),
        vehicles: points.map(p => ({ ...p, value: Math.floor(Math.random() * 30) })),
        ppeBreaches: points.map(p => ({ ...p, value: Math.floor(Math.random() * 10) })),
        zoneEntries: points.map(p => ({ ...p, value: Math.floor(Math.random() * 8) }))
    };
}

// Enhanced mock data for chart modal with all four data series
export function getMockChartModalData(timeRange: TimeRange): {
    labels: string[];
    persons: number[];
    vehicles: number[];
    ppeBreaches: number[];
    zoneEntries: number[];
} {
    const labels: string[] = [];
    const persons: number[] = [];
    const vehicles: number[] = [];
    const ppeBreaches: number[] = [];
    const zoneEntries: number[] = [];

    const hoursDiff = Math.floor((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60));

    if (hoursDiff <= 24) {
        // Day view - hourly data
        for (let i = 0; i < 24; i++) {
            labels.push(`${i.toString().padStart(2, '0')}:00`);
            persons.push(Math.floor(Math.random() * 50) + 10);
            vehicles.push(Math.floor(Math.random() * 30) + 5);
            ppeBreaches.push(Math.floor(Math.random() * 10));
            zoneEntries.push(Math.floor(Math.random() * 8));
        }
    } else if (hoursDiff <= 168) {
        // Week view - daily data (Monday to Sunday) with actual dates
        const startDate = new Date(timeRange.start);
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        for (let i = 0; i < 7; i++) {
            const date = new Date(startDate);
            date.setDate(date.getDate() + i);
            const dayName = days[date.getDay()];
            const monthName = months[date.getMonth()];
            labels.push(`${dayName} ${monthName} ${date.getDate()}`);
            persons.push(Math.floor(Math.random() * 200) + 50);
            vehicles.push(Math.floor(Math.random() * 100) + 20);
            ppeBreaches.push(Math.floor(Math.random() * 30) + 5);
            zoneEntries.push(Math.floor(Math.random() * 20) + 3);
        }
    } else if (hoursDiff <= 744) { // Approximately one month
        // Month view - daily data with formatted dates
        const startDate = new Date(timeRange.start);
        const endDate = new Date(timeRange.end);
        const numDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        for (let i = 0; i < numDays; i++) {
            const date = new Date(startDate);
            date.setDate(date.getDate() + i);
            const monthName = months[date.getMonth()];
            labels.push(`${monthName} ${date.getDate()}`);
            persons.push(Math.floor(Math.random() * 200) + 50);
            vehicles.push(Math.floor(Math.random() * 100) + 20);
            ppeBreaches.push(Math.floor(Math.random() * 30) + 5);
            zoneEntries.push(Math.floor(Math.random() * 20) + 3);
        }
    } else {
        // All time - weekly data
        const numWeeks = 12;
        for (let i = 0; i < numWeeks; i++) {
            labels.push(`Week ${i + 1}`);
            persons.push(Math.floor(Math.random() * 500) + 100);
            vehicles.push(Math.floor(Math.random() * 300) + 50);
            ppeBreaches.push(Math.floor(Math.random() * 80) + 20);
            zoneEntries.push(Math.floor(Math.random() * 60) + 15);
        }
    }

    return { labels, persons, vehicles, ppeBreaches, zoneEntries };
}

// Future API functions (to be implemented when backend endpoints are ready)
export async function fetchStats(timeRange: TimeRange): Promise<DashboardStats> {
    // TODO: Replace with actual API call
    // const response = await fetch(`/api/stats?start=${timeRange.start.toISOString()}&end=${timeRange.end.toISOString()}`);
    // return await response.json();

    // For now, return mock data
    return getMockStats(timeRange);
}

export async function fetchChartData(timeRange: TimeRange): Promise<ChartData> {
    // TODO: Replace with actual API call
    // const response = await fetch(`/api/chart-data?start=${timeRange.start.toISOString()}&end=${timeRange.end.toISOString()}`);
    // return await response.json();

    // For now, return mock data
    return getMockChartData(timeRange);
}

export async function fetchDetectionBarChartData(timeRange: TimeRange): Promise<DetectionBarChartData> {
    // TODO: Replace with actual API call
    // const response = await fetch(`/api/detection-chart?start=${timeRange.start.toISOString()}&end=${timeRange.end.toISOString()}`);
    // return await response.json();

    // For now, return mock data
    return getMockDetectionBarChartData(timeRange);
}

export async function fetchPPEComplianceData(): Promise<PPEComplianceData> {
    // TODO: Replace with actual API call
    // const response = await fetch(`/api/ppe-compliance`);
    // return await response.json();

    // For now, return mock data
    return getMockPPEComplianceData();
}

// ============================================
// API Functions for Events
// ============================================

/**
 * Fetch events for a specific location within a date range
 * @param locationId - The ID of the location to fetch events for
 * @param startDate - Start date in ISO format (YYYY-MM-DD or ISO string)
 * @param endDate - End date in ISO format (YYYY-MM-DD or ISO string)
 * @returns Promise<EventsResponse> - The events data
 */
export async function fetchEventsByLocationAndTime(
    locationId: number,
    startDate: string,
    endDate: string
): Promise<EventsResponse> {
    try {
        const response = await fetch(
            `${API_BASE_URL}/events_time?location_id=${locationId}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`
        );

        if (!response.ok) {
            throw new Error(`Failed to fetch events: ${response.statusText}`);
        }

        const data = await response.json();

        // Transform the data if needed (backend might return different format)
        const events: Event[] = Array.isArray(data) ? data : data.events || [];

        return {
            events,
            count: events.length
        };
    } catch (error) {
        console.error('Error fetching events:', error);
        throw error;
    }
}

/**
 * Fetch events for a specific location using TimeRange object
 * @param locationId - The ID of the location to fetch events for
 * @param timeRange - TimeRange object containing start and end dates
 * @returns Promise<EventsResponse> - The events data
 */
export async function fetchEventsForLocation(
    locationId: number,
    timeRange: TimeRange
): Promise<EventsResponse> {
    // Convert dates to ISO string format (YYYY-MM-DDTHH:mm:ss)
    const startDate = timeRange.start.toISOString();
    const endDate = timeRange.end.toISOString();

    return fetchEventsByLocationAndTime(locationId, startDate, endDate);
}

// ============================================
// Data Transformation Functions
// ============================================

/**
 * Calculate dashboard statistics from events data
 * @param events - Array of Event objects
 * @returns DashboardStats object
 */
export function calculateStatsFromEvents(events: Event[]): DashboardStats {
    let detectedPersons = 0;
    let detectedVehicles = 0;
    let ppeBreaches = 0;
    let helmetBreaches = 0;
    let vestBreaches = 0;
    let riskZoneEntries = 0;

    // Track unique objects to avoid counting duplicates
    const uniquePersons = new Set<number>();
    const uniqueVehicles = new Set<number>();
    // Track unique persons with PPE breaches (one breach per person, regardless of what's missing)
    const uniquePPEBreaches = new Set<number>();
    // Track zone entry breakdown
    const zoneEntryBreakdown = new Map<number, number>();

    events.forEach(event => {
        // Assuming object_id differentiates between persons and vehicles
        // You may need to adjust this logic based on your actual data structure

        // For now, assuming all events are person-related (adjust as needed)
        uniquePersons.add(event.object_id);

        // Check for PPE breaches (missing helmet or vest)
        // Only count once per unique person (object_id)
        if (!event.has_helmet || !event.has_vest) {
            uniquePPEBreaches.add(event.object_id);
        }

        // Count helmet breaches specifically
        if (!event.has_helmet) {
            helmetBreaches++;
        }

        // Count vest breaches specifically
        if (!event.has_vest) {
            vestBreaches++;
        }

        // Count risk zone entries (this assumes all events are zone entries)
        // You might want to add a flag in your Event type to distinguish entry types
        if (event.zone_id != null) {
            riskZoneEntries++;
            // Track which zones were entered
            const currentCount = zoneEntryBreakdown.get(event.zone_id) || 0;
            zoneEntryBreakdown.set(event.zone_id, currentCount + 1);
        }
    });

    detectedPersons = uniquePersons.size;
    detectedVehicles = uniqueVehicles.size;
    ppeBreaches = uniquePPEBreaches.size; // Count unique persons with breaches

    return {
        detectedPersons,
        detectedVehicles,
        ppeBreaches,
        helmetBreaches,
        vestBreaches,
        riskZoneEntries: riskZoneEntries,
        zoneEntryBreakdown
    };
}

/**
 * Calculate PPE compliance data from events
 * @param events - Array of Event objects
 * @returns PPEComplianceData object
 */
export function calculatePPEComplianceFromEvents(events: Event[]): PPEComplianceData {
    // Track unique objects and their PPE status
    // Use a Map to store the most recent PPE status for each object_id
    const objectPPEStatus = new Map<number, { hasHelmet: boolean; hasVest: boolean }>();

    events.forEach(event => {
        // Store or update the PPE status for this object
        objectPPEStatus.set(event.object_id, {
            hasHelmet: event.has_helmet,
            hasVest: event.has_vest
        });
    });

    // Now count unique objects by their PPE compliance status
    let compliant = 0;
    let missingHardHat = 0;
    let missingVest = 0;
    let missingBoth = 0;

    objectPPEStatus.forEach(status => {
        if (status.hasHelmet && status.hasVest) {
            compliant++;
        } else if (!status.hasHelmet && !status.hasVest) {
            missingBoth++;
        } else if (!status.hasHelmet) {
            missingHardHat++;
        } else if (!status.hasVest) {
            missingVest++;
        }
    });

    return {
        compliant,
        missingHardHat,
        missingVest,
        missingBoth
    };
}

/**
 * Group events by time intervals and count them
 * @param events - Array of Event objects
 * @param timeRange - The time range for grouping
 * @returns DetectionBarChartData object
 */
export function createBarChartDataFromEvents(
    events: Event[],
    timeRange: TimeRange
): DetectionBarChartData {
    const labels: string[] = [];
    const persons: number[] = [];
    const vehicles: number[] = [];

    const hoursDiff = Math.floor((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60));

    // Group events by time intervals
    if (hoursDiff <= 24) {
        // Day view - hourly data
        const hourCounts = new Array(24).fill(0);

        events.forEach(event => {
            const eventDate = new Date(event.time);
            const hour = eventDate.getHours();
            hourCounts[hour]++;
        });

        for (let i = 0; i < 24; i++) {
            labels.push(`${i}:00`);
            persons.push(hourCounts[i]);
            vehicles.push(0); // Adjust based on your data
        }
    } else if (hoursDiff <= 168) {
        // Week view - daily data (Monday to Sunday) with actual dates
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const numDays = 7;
        const dayCounts = new Array(numDays).fill(0);

        // Start from the beginning of the time range (should be Monday)
        const startDate = new Date(timeRange.start);

        // Create a map to track counts for each specific date
        const dateCountMap = new Map<string, number>();

        events.forEach(event => {
            const eventDate = new Date(event.time);
            // Calculate which day index (0-6) this event belongs to
            const dayDiff = Math.floor((eventDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
            if (dayDiff >= 0 && dayDiff < numDays) {
                dayCounts[dayDiff]++;
            }
        });

        // Generate labels with day names and dates
        for (let i = 0; i < numDays; i++) {
            const date = new Date(startDate);
            date.setDate(date.getDate() + i);
            const dayName = days[date.getDay()];
            const monthName = months[date.getMonth()];
            labels.push(`${dayName} ${monthName} ${date.getDate()}`);
            persons.push(dayCounts[i]);
            vehicles.push(0);
        }
    } else if (hoursDiff <= 720) {
        // Month view - daily data with formatted dates
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const numDays = Math.ceil(hoursDiff / 24);
        const dayCounts = new Array(numDays).fill(0);

        events.forEach(event => {
            const eventDate = new Date(event.time);
            const dayDiff = Math.floor((eventDate.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60 * 24));
            if (dayDiff >= 0 && dayDiff < numDays) {
                dayCounts[dayDiff]++;
            }
        });

        for (let i = 0; i < numDays; i++) {
            const date = new Date(timeRange.start);
            date.setDate(date.getDate() + i);
            const monthName = months[date.getMonth()];
            labels.push(`${monthName} ${date.getDate()}`);
            persons.push(dayCounts[i]);
            vehicles.push(0);
        }
    } else {
        // All time - weekly data
        const numWeeks = Math.ceil(hoursDiff / 168);
        const weekCounts = new Array(numWeeks).fill(0);

        events.forEach(event => {
            const eventDate = new Date(event.time);
            const weekDiff = Math.floor((eventDate.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60 * 24 * 7));
            if (weekDiff >= 0 && weekDiff < numWeeks) {
                weekCounts[weekDiff]++;
            }
        });

        for (let i = 0; i < numWeeks; i++) {
            labels.push(`Week ${i + 1}`);
            persons.push(weekCounts[i]);
            vehicles.push(0);
        }
    }

    return { labels, persons, vehicles };
}

/**
 * Create time series chart data from events
 * @param events - Array of Event objects
 * @param timeRange - The time range for the chart
 * @returns ChartData object
 */
export function createChartDataFromEvents(
    events: Event[],
    timeRange: TimeRange
): ChartData {
    const hoursDiff = Math.floor((timeRange.end.getTime() - timeRange.start.getTime()) / (1000 * 60 * 60));

    // Determine number of intervals based on time range
    let numPoints: number;
    let intervalMs: number;

    if (hoursDiff <= 24) {
        // Day view - 24 hourly intervals
        numPoints = 24;
        intervalMs = 60 * 60 * 1000; // 1 hour
    } else if (hoursDiff <= 168) {
        // Week view - 7 daily intervals
        numPoints = 7;
        intervalMs = 24 * 60 * 60 * 1000; // 1 day
    } else if (hoursDiff <= 720) {
        // Month view - daily intervals
        numPoints = Math.ceil(hoursDiff / 24);
        intervalMs = 24 * 60 * 60 * 1000; // 1 day
    } else {
        // All time - weekly intervals
        numPoints = Math.ceil(hoursDiff / 168);
        intervalMs = 7 * 24 * 60 * 60 * 1000; // 1 week
    }

    const persons: ChartDataPoint[] = [];
    const vehicles: ChartDataPoint[] = [];
    const ppeBreaches: ChartDataPoint[] = [];
    const zoneEntries: ChartDataPoint[] = [];

    for (let i = 0; i < numPoints; i++) {
        const intervalStart = new Date(timeRange.start.getTime() + (i * intervalMs));
        const intervalEnd = new Date(timeRange.start.getTime() + ((i + 1) * intervalMs));

        // Count events in this interval
        const uniquePersonsInInterval = new Set<number>();
        const uniqueVehiclesInInterval = new Set<number>();
        const uniquePPEBreachesInInterval = new Set<number>();
        let entryCount = 0;

        events.forEach(event => {
            const eventTime = new Date(event.time).getTime();
            if (eventTime >= intervalStart.getTime() && eventTime < intervalEnd.getTime()) {
                // Track unique persons
                uniquePersonsInInterval.add(event.object_id);

                // Count zone entries only when zone_id is not null
                if (event.zone_id != null) {
                    entryCount++;
                }

                // Track unique persons with PPE breaches (one breach per person)
                if (!event.has_helmet || !event.has_vest) {
                    uniquePPEBreachesInInterval.add(event.object_id);
                }
            }
        });

        const timestamp = intervalStart.toISOString();
        persons.push({ timestamp, value: uniquePersonsInInterval.size });
        vehicles.push({ timestamp, value: uniqueVehiclesInInterval.size });
        ppeBreaches.push({ timestamp, value: uniquePPEBreachesInInterval.size });
        zoneEntries.push({ timestamp, value: entryCount });
    }

    return { persons, vehicles, ppeBreaches, zoneEntries };
}
