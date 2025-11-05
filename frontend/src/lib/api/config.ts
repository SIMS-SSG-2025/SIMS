export type Zone = {
    zone_id?: number;
    points: { x: number; y: number }[];
    name: string;
};

export type Config = {
    locationId: number;
    locationName: string;
    zones: Zone[];
    snapshotPath: string;
};

export type LocationSummary = {
    locationId: number;
    locationName: string;
    zoneCount: number;
};
// Jetson
export const API_BASE_URL = "http://10.10.67.44:8000";
// Local
//export const API_BASE_URL = "http://127.0.0.1:8000";

export async function fetchCurrentConfig(): Promise<Config | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/config/current`);
        const data = await response.json();

        if (data.status === "success" && data.config) {
            // Add cache-busting timestamp to snapshot path
            const snapshotUrl = `${API_BASE_URL}${data.config.snapshotPath}`;
            const cacheBuster = `?t=${Date.now()}`;

            return {
                locationId: data.config.locationId,
                locationName: data.config.locationName,
                zones: data.config.zones.map((z: any) => ({
                    zone_id: z.zone_id,
                    points: z.coords,
                    name: z.name
                })),
                snapshotPath: `${snapshotUrl}${cacheBuster}`
            };
        }
        return null;
    } catch (error) {
        console.error("Error fetching config:", error);
        return null;
    }
}

export async function fetchAllLocations(): Promise<LocationSummary[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/config/locations`);
        const data = await response.json();

        if (data.status === "success" && data.locations) {
            return data.locations;
        }
        return [];
    } catch (error) {
        console.error("Error fetching locations:", error);
        return [];
    }
}

export async function fetchConfigByLocation(locationId: number): Promise<Config | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/config/location/${locationId}`);
        const data = await response.json();

        if (data.status === "success" && data.config) {
            // Add cache-busting timestamp to snapshot path
            const snapshotUrl = `${API_BASE_URL}${data.config.snapshotPath}`;
            const cacheBuster = `?t=${Date.now()}`;

            return {
                locationId: data.config.locationId,
                locationName: data.config.locationName,
                zones: data.config.zones.map((z: any) => ({
                    zone_id: z.zone_id,
                    points: z.coords,
                    name: z.name
                })),
                snapshotPath: `${snapshotUrl}${cacheBuster}`
            };
        }
        return null;
    } catch (error) {
        console.error("Error fetching config by location:", error);
        return null;
    }
}

export async function deleteLocationConfig(locationId: number): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/config/location/${locationId}`, {
            method: "DELETE"
        });
        return response.ok;
    } catch (error) {
        console.error("Error deleting location config:", error);
        return false;
    }
}

export async function saveConfig(locationName: string, zones: Zone[]): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/setup_config`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                locationName,
                zones
            })
        });

        const result = await response.json();
        return result.status === "success";
    } catch (error) {
        console.error("Error saving config:", error);
        return false;
    }
}

export async function fetchSnapshot() {
    try {
        // Add cache-busting timestamp to prevent browser caching
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(`${API_BASE_URL}/snapshot${cacheBuster}`);
        if (!response.ok) {
            throw new Error(`Error fetching snapshot: ${response.statusText}`);
        }

        const blob = await response.blob();
        const blobURL = URL.createObjectURL(blob);
        return blobURL;

    } catch (err: any) {
        console.error('Error fetching snapshot:', err);
        return "";
    }
}

export async function startSystem() {
    try {
        const response = await fetch(`${API_BASE_URL}/system/start`, {
            method: "POST"
        });
        const startResult = await response.json();
        return startResult
    } catch (error) {
        console.error("Error starting system:", error);
        return false;
    }
}

export async function stopSystem() {
    try {
        const response = await fetch(`${API_BASE_URL}/system/stop`, {
            method: "POST"
        });
        const stopResult = await response.json();
        return stopResult
    } catch (error) {
        console.error("Error stopping system:", error);
        return false;
    }
}

export async function getSystemStatus(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/system/status`);
        const result = await response.json();
        return result.status === true;
    } catch (error) {
        console.error("Error getting system status:", error);
        return false;
    }
}

export async function activateLocation(locationId: number): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/config/activate/${locationId}`, {
            method: "POST"
        });

        const result = await response.json();
        return result.status === "success";
    } catch (error) {
        console.error("Error activating location:", error);
        return false;
    }
}

export type ObjectPosition = {
    object_id: number;
    location: number;
    x: number;
    y: number;
    time: string;
};

export async function fetchObjectPositions(
    locationId: number,
    startDate: string,
    endDate: string
): Promise<ObjectPosition[]> {
    try {
        const response = await fetch(
            `${API_BASE_URL}/object_positions?location_id=${locationId}&start_date=${startDate}&end_date=${endDate}`
        );
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching object positions:", error);
        return [];
    }
}
