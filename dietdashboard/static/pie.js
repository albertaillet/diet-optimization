import * as d3 from './d3.js';

export function makePie(container, data, labels, totalCalories) {
  const width = container.clientWidth;
  const height = 150;
  const radius = Math.min(width, height) / 2.8;

  const color = d3.scaleOrdinal()
    .domain(data)
    .range([d3.schemeTableau10[2], d3.schemeTableau10[4], d3.schemeTableau10[8]]);

  // Create pie layout
  const pie = d3.pie()
    .padAngle(0.02);

  // Create arc generators
  const arc = d3.arc()
    .innerRadius(radius * 0.4) // Larger inner circle to fit text
    .outerRadius(radius)
    .cornerRadius(0); // No rounded corners

  d3.select(container).selectAll("*").remove();

  // Create SVG
  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('height', height)
    .append('g')
    .attr('transform', `translate(${width/2}, ${height/2})`);

  // Create pie slices with data
  const arcs = pie(data);

  // Add arcs with hover effects but no animation
  const paths = svg.selectAll('path')
    .data(arcs)
    .enter()
    .append('path')
    .attr('d', arc)
    .attr('fill', (d, i) => color(i))
    .style('cursor', 'pointer')
    .on('mouseover', function(event, d) {
      d3.select(this)
        .attr('opacity', 0.85);
    })
    .on('mouseout', function(event, d) {
      d3.select(this)
        .attr('opacity', 1);
    });

  svg.selectAll('text.value-label')
    .data(arcs)
    .enter()
    .append('text')
    .attr('class', 'value-label')
    .attr('transform', d => `translate(${arc.centroid(d)})`)
    .attr('dy', '.35em')
    .attr('text-anchor', 'middle')
    .style('font-size', '11px')
    .style('font-weight', '500')
    .style('fill', 'white')
    .style('pointer-events', 'none')
    .text((d, i) => `${labels[i]}`);

  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '0em')
    .style('font-size', '12px')
    .style('font-weight', 'bold')
    .style('fill', '#333')
    .text(`${Math.round(totalCalories)}`);

  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .style('font-size', '10px')
    .style('fill', '#666')
    .text('kcal');
}
