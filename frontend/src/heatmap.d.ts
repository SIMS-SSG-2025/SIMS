declare module 'heatmap.js' {
    export interface HeatmapConfiguration {
        container: HTMLElement;
        radius?: number;
        maxOpacity?: number;
        minOpacity?: number;
        blur?: number;
        gradient?: Record<string, string>;
    }

    export interface HeatmapDataPoint {
        x: number;
        y: number;
        value: number;
    }

    export interface HeatmapData {
        max: number;
        data: HeatmapDataPoint[];
    }

    export interface Heatmap {
        setData(data: HeatmapData): void;
        addData(data: HeatmapDataPoint | HeatmapDataPoint[]): void;
        getData(): HeatmapData;
        getDataURL(): string;
        repaint(): void;
    }

    export function create(config: HeatmapConfiguration): Heatmap;

    const h337: {
        create: (config: HeatmapConfiguration) => Heatmap;
    };

    export default h337;
}
