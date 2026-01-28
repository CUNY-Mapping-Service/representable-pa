<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import * as d3 from 'd3';
import type { Feature as GeoJSONFeature, Geometry } from 'geojson';

const props = defineProps<{
  geometry?: GeoJSONFeature<Geometry> | null;
  fillColor?: string | null;
  outlineColor?: string | null;

}>();

const svgEl = ref<SVGSVGElement | null>(null);

const draw = () => {
  if (!svgEl.value || !props.geometry) return;

  const width = svgEl.value.clientWidth || 200;
  const height = 100;

  const svg = d3.select(svgEl.value);
  svg.selectAll('*').remove();

  const margin = { top: 10, right: 5, bottom: 10, left: 5 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const g = svg
    .attr('viewBox', `0 0 ${width} ${height}`)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const projection = d3
    .geoIdentity()
    .reflectY(true)
    .fitSize([innerWidth, innerHeight], props.geometry as any);

  const path = d3.geoPath(projection as any);

  g.append('path')
    .datum(props.geometry)
    .attr('d', path as any)
    .attr('fill', (props.fillColor ?? '#787878') + '33')
    .attr('stroke', props.outlineColor ?? 'darkgray')
    .attr('stroke-width', 1);
};

onMounted(draw);
watch(
  () => props.geometry,
  () => draw(),
  { deep: true }
);
</script>

<template>
  <svg ref="svgEl" :height="100" style="width: 100%; display: block;"></svg>
</template>