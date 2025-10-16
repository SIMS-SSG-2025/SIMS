import { API_BASE_URL } from './config';

// Types for dashboard statistics
export interface DashboardStats {
    detectedPersons: number;
    detectedVehicles: number;
    ppeBreaches: number;
    forbiddenZoneEntries: number;
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
export function calculateTimeRange(option: TimeRangeOption, customRange?: TimeRange): TimeRange {
    const end = new Date();
    let start = new Date();

    switch (option) {
        case 'day':
            start.setHours(0, 0, 0, 0);
            break;
        case 'week':
            start.setDate(end.getDate() - 7);
            start.setHours(0, 0, 0, 0);
            break;
        case 'month':
            start.setMonth(end.getMonth() - 1);
            start.setHours(0, 0, 0, 0);
            break;
        case 'all':
            start = new Date(2020, 0, 1); // Default to a far past date
            break;
        case 'custom':
            if (customRange) {
                return customRange;
            }
            break;
    }

    return { start, end };
}

// Mock data for development (to be replaced with API calls)
export function getMockStats(timeRange: TimeRange): DashboardStats {
    // This is placeholder data - will be replaced with actual API call
    return {
        detectedPersons: Math.floor(Math.random() * 1000) + 100,
        detectedVehicles: Math.floor(Math.random() * 500) + 50,
        ppeBreaches: Math.floor(Math.random() * 50) + 5,
        forbiddenZoneEntries: Math.floor(Math.random() * 30) + 2
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
    let forbiddenZoneEntries = 0;

    // Track unique objects to avoid counting duplicates
    const uniquePersons = new Set<number>();
    const uniqueVehicles = new Set<number>();

    events.forEach(event => {
        // Assuming object_id differentiates between persons and vehicles
        // You may need to adjust this logic based on your actual data structure

        // For now, assuming all events are person-related (adjust as needed)
        uniquePersons.add(event.object_id);

        // Check for PPE breaches (missing helmet or vest)
        if (!event.has_helmet || !event.has_vest) {
            ppeBreaches++;
        }

        // Count forbidden zone entries (this assumes all events are zone entries)
        // You might want to add a flag in your Event type to distinguish entry types
        forbiddenZoneEntries++;
    });

    detectedPersons = uniquePersons.size;
    detectedVehicles = uniqueVehicles.size;

    return {
        detectedPersons,
        detectedVehicles,
        ppeBreaches,
        forbiddenZoneEntries
    };
}

/**
 * Calculate PPE compliance data from events
 * @param events - Array of Event objects
 * @returns PPEComplianceData object
 */
export function calculatePPEComplianceFromEvents(events: Event[]): PPEComplianceData {
    let compliant = 0;
    let missingHardHat = 0;
    let missingVest = 0;
    let missingBoth = 0;

    events.forEach(event => {
        if (event.has_helmet && event.has_vest) {
            compliant++;
        } else if (!event.has_helmet && !event.has_vest) {
            missingBoth++;
        } else if (!event.has_helmet) {
            missingHardHat++;
        } else if (!event.has_vest) {
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
        // Week view - daily data
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const dayCounts = new Array(7).fill(0);

        events.forEach(event => {
            const eventDate = new Date(event.time);
            const dayOfWeek = eventDate.getDay();
            dayCounts[dayOfWeek]++;
        });

        for (let i = 0; i < 7; i++) {
            labels.push(days[i]);
            persons.push(dayCounts[i]);
            vehicles.push(0);
        }
    } else if (hoursDiff <= 720) {
        // Month view - daily data
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
            labels.push(`${date.getMonth() + 1}/${date.getDate()}`);
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
    const numPoints = Math.min(Math.max(hoursDiff, 12), 48); // Between 12 and 48 points
    const intervalMs = (timeRange.end.getTime() - timeRange.start.getTime()) / numPoints;

    const persons: ChartDataPoint[] = [];
    const vehicles: ChartDataPoint[] = [];
    const ppeBreaches: ChartDataPoint[] = [];
    const zoneEntries: ChartDataPoint[] = [];

    for (let i = 0; i < numPoints; i++) {
        const intervalStart = new Date(timeRange.start.getTime() + (i * intervalMs));
        const intervalEnd = new Date(timeRange.start.getTime() + ((i + 1) * intervalMs));

        // Count events in this interval
        let personCount = 0;
        let vehicleCount = 0;
        let breachCount = 0;
        let entryCount = 0;

        events.forEach(event => {
            const eventTime = new Date(event.time).getTime();
            if (eventTime >= intervalStart.getTime() && eventTime < intervalEnd.getTime()) {
                personCount++;
                entryCount++;

                if (!event.has_helmet || !event.has_vest) {
                    breachCount++;
                }
            }
        });

        const timestamp = intervalStart.toISOString();
        persons.push({ timestamp, value: personCount });
        vehicles.push({ timestamp, value: vehicleCount });
        ppeBreaches.push({ timestamp, value: breachCount });
        zoneEntries.push({ timestamp, value: entryCount });
    }

    return { persons, vehicles, ppeBreaches, zoneEntries };
}
