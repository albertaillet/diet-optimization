import * as d3 from './d3.js';

export function makePie(container) {
  const protein = Number(container.dataset.protein);
  const carbohydrate = Number(container.dataset.carbohydrate);
  const fat = Number(container.dataset.fat);
  const data = [protein, carbohydrate, fat];
  const labels = ['Protein', 'Carbs', 'Fat'];
  console.log(data);

  // Set dimensions
  const width = container.clientWidth;
  const height = 150;
  const radius = Math.min(width, height) / 2.5;

  // Create color scale
  const color = d3.scaleOrdinal()
    .domain(data)
    .range(["#66c2a5", "#fc8d62", "#8da0cb"]);

  // Create pie layout
  const pie = d3.pie()
    .sort(null);

  // Create arc generators
  const arc = d3.arc()
    .innerRadius(0)
    .outerRadius(radius);

  // Create a separate arc for label positioning
  const labelArc = d3.arc()
    .innerRadius(radius * 0.7)
    .outerRadius(radius * 1.1);

  // Create SVG
  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', height)
    .append('g')
    .attr('transform', `translate(${width/2}, ${height/2})`);

  // Create pie slices with data
  const arcs = pie(data);

  // Add arcs
  svg.selectAll('path')
    .data(arcs)
    .enter()
    .append('path')
    .attr('d', arc)
    .attr('fill', (d, i) => color(i));

  // Add labels for each segment
  svg.selectAll('text.label')
    .data(arcs)
    .enter()
    .append('text')
    .attr('class', 'label')
    .attr('transform', d => {
      // Position labels slightly outside the arc
      const pos = labelArc.centroid(d);
      // Move labels further out for better positioning
      const x = pos[0] * 1.3;
      const y = pos[1] * 1.3;
      return `translate(${x}, ${y})`;
    })
    .attr('dy', '.35em')
    .attr('text-anchor', d => {
      // Align text based on position around the circle
      const midangle = d.startAngle + (d.endAngle - d.startAngle) / 2;
      return (midangle < Math.PI ? 'start' : 'end');
    })
    .style('font-size', '10px')
    .text((d, i) => labels[i]);
}

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('pie');
  console.log(container);
  makePie(container);
});
