// Types for dashboard statistics
export interface DashboardStats {
    detectedPersons: number;
    detectedVehicles: number;
    ppeBreaches: number;
    forbiddenZoneEntries: number;
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
