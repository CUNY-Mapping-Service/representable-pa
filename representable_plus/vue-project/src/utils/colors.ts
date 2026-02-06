import * as d3 from "d3";

export function getTurfColor(index: number): string {
    const colors = d3.schemeTableau10;
    return colors[index % colors.length] ?? '';
}

export function getTurfOutlineColor(fillColor: string): string {
    const d3Color = d3.color(fillColor);
    if (d3Color) {
        return d3Color.darker(1.5).formatHex();
    }
    return '#333';
}