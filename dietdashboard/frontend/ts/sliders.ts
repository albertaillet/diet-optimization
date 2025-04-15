import * as d3 from "./d3";
import { handleOptimizationInputs, isVisible } from "./index";

/**
 * Common configuration values
 */
const CONFIG = {
  margin: { top: 5, right: 10, bottom: 20, left: 10 },
  svgHeight: 50,
  nTicks: 10,
  barHeight: 10,
  brushHeight: 4,
  handleRadius: 7
};

/**
 * Creates an SVG element for a slider with D3
 */
function createSliderSVG(
  container: HTMLElement,
  min: number,
  max: number
): {
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  x: d3.ScaleLinear<number, number>;
  width: number;
  height: number;
} {
  const svg = d3
    .select(container)
    .append("svg")
    .attr("width", "100%")
    .attr("height", CONFIG.svgHeight)
    .attr("data-nutrient", container.id);

  // Store configuration in data attributes
  svg.attr("data-domain-min", min).attr("data-domain-max", max).attr("data-container-id", container.id);

  const width = container.clientWidth - CONFIG.margin.left - CONFIG.margin.right;
  const height = CONFIG.svgHeight - CONFIG.margin.top - CONFIG.margin.bottom;

  svg.attr("data-range-width", width);

  // Create scale
  const x = d3.scaleLinear().domain([min, max]).range([0, width]);

  return { svg, x, width, height };
}

/**
 * Adds axis to the slider
 */
function createSliderAxis(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  x: d3.ScaleLinear<number, number>,
  height: number
): {
  g: d3.Selection<SVGGElement, unknown, null, undefined>;
  axisYPosition: number;
  barYPosition: number;
  barGroup: d3.Selection<SVGGElement, unknown, null, undefined>;
} {
  const g = svg.append("g").attr("transform", `translate(${CONFIG.margin.left},${CONFIG.margin.top})`);

  const axisYPosition = height;
  const xAxis = d3.axisBottom(x).ticks(CONFIG.nTicks).tickSize(6).tickPadding(3);

  g.append("g")
    .attr("class", "x axis")
    .attr("transform", `translate(0,${axisYPosition})`)
    .call(xAxis)
    .selectAll("text")
    .style("text-anchor", "middle");

  // Calculate bar position
  const barYPosition = axisYPosition - CONFIG.barHeight - 2;

  svg.attr("data-bar-height", CONFIG.barHeight).attr("data-bar-y-position", barYPosition);

  const barGroup = g.append("g").attr("class", "stacked-bar");

  return { g, axisYPosition, barYPosition, barGroup };
}

/**
 * Adds brush interaction to the slider
 */
function createSliderBrush(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  x: d3.ScaleLinear<number, number>,
  axisYPosition: number,
  width: number,
  container: HTMLElement,
  lower: number,
  upper: number
): void {
  const brushYPosition = axisYPosition - CONFIG.brushHeight / 2;

  const brushSelection = d3
    .brushX()
    .extent([
      [0, brushYPosition],
      [width, brushYPosition + CONFIG.brushHeight]
    ])
    .on("brush", brushed)
    .on("end", brushended);

  const brushGroup = g.append("g").attr("class", "brush").call(brushSelection);

  // Add custom handles
  const handle = brushGroup
    .selectAll(".handle--custom")
    .data([{ type: "w" }, { type: "e" }])
    .enter()
    .append("g")
    .attr("class", "handle--custom")
    .attr("cursor", "ew-resize");

  handle.append("circle").attr("r", CONFIG.handleRadius).attr("cy", axisYPosition);

  // Set initial brush position
  brushGroup.call(brushSelection.move, [x(lower), x(upper)]);

  function brushed(event: d3.D3BrushEvent<unknown>) {
    if (event.selection) {
      handle.attr("transform", (_d, i) => `translate(${event.selection![i]}, 0)`);
    }
  }

  function brushended(event: d3.D3BrushEvent<unknown>) {
    if (!event.sourceEvent) return;
    const [lower, upper] = event.selection?.map(v => x.invert(v)).map(Math.round);
    d3.select(this).transition().call(brushSelection.move, [lower, upper].map(x));
    container.dataset.lower = String(lower);
    container.dataset.upper = String(upper);
    handleOptimizationInputs();
  }
}

/**
 * Initializes or updates a slider
 */
function setupSlider(container: HTMLElement, isUpdate = false): void {
  const min = Number(container.dataset.min);
  const max = Number(container.dataset.max);
  let lower = Number(container.dataset.lower);
  let upper = Number(container.dataset.upper);

  if (isUpdate) {
    lower = Math.max(min, Math.min(lower, max));
    upper = Math.max(min, Math.min(upper, max));
    container.dataset.lower = String(lower);
    container.dataset.upper = String(upper);

    const existingSvg = container.querySelector("svg");
    if (existingSvg) {
      existingSvg.remove();
    }
  }

  const { svg, x, width, height } = createSliderSVG(container, min, max);
  const { g, axisYPosition, barYPosition, barGroup } = createSliderAxis(svg, x, height);

  createSliderBrush(g, x, axisYPosition, width, container, lower, upper);
}

/**
 * Initialize all sliders on the page
 */
function initializeSliders(): void {
  const containers = document.querySelectorAll<HTMLElement>(".slider-container");
  containers.forEach(container => setupSlider(container));
}

/**
 * Update the range of a slider
 */
export function updateSliderRange(sliderId: string, newMin: number, newMax: number): void {
  const container = document.getElementById(sliderId);
  if (!container) return;

  container.dataset.min = String(newMin);
  container.dataset.max = String(newMax);

  setupSlider(container, true);
}

/**
 * Update the bar charts in sliders with product data
 */
export function updateBars(products: Array<Record<string, any>>): void {
  const containers = document.querySelectorAll(".slider-container");

  containers.forEach(container => {
    // Skip hidden containers
    if (!isVisible(container)) return;

    const min = Number(container.dataset.min);
    const max = Number(container.dataset.max);
    const nutrientName = container.id;

    const svgElement = container.querySelector("svg");
    if (!svgElement) return;

    const svg = d3.select(svgElement);
    const rangeWidth = Number(svg.attr("data-range-width"));
    const barYPosition = Number(svg.attr("data-bar-y-position"));
    const barHeight = Number(svg.attr("data-bar-height"));

    const x = d3.scaleLinear().domain([min, max]).range([0, rangeWidth]);
    const barGroup = svg.select(".stacked-bar");
    const segments = createSegmentsData(products, nutrientName);
    updateSegments(barGroup, segments, x, barYPosition, barHeight);
  });
}

/**
 * Create segment data from products for a specific nutrient
 */
function createSegmentsData(products: Array<Record<string, any>>, nutrientName: string) {
  const segments = products.map((product, i) => ({
    i,
    id: product.id,
    name: product.product_name,
    level: Number(product[nutrientName]),
    startValue: 0,
    endValue: 0
  }));

  let cum = 0;
  segments.forEach(d => {
    d.startValue = cum;
    cum += d.level;
    d.endValue = cum;
  });

  return segments;
}

/**
 * Update the segments visualization with new data
 */
function updateSegments(
  barGroup: d3.Selection<SVGGElement, unknown, null, undefined>,
  segments: Array<any>,
  x: d3.ScaleLinear<number, number>,
  barYPosition: number,
  barHeight: number
): void {
  const segmentGroups = barGroup.selectAll(".segment-group").data(segments);

  // EXIT selection: Remove old elements
  segmentGroups.exit().transition().duration(100).style("opacity", 0).remove();

  // ENTER selection: Create new elements
  const segmentGroupsEnter = segmentGroups.enter().append("g").attr("class", "segment-group");

  // Append rectangles to entering segments
  segmentGroupsEnter.append("rect").attr("class", "segment").attr("y", barYPosition).attr("height", barHeight).attr("width", 0); // Start with zero width for transition

  segmentGroupsEnter
    .append("text")
    .attr("class", "segment-label")
    .attr("y", barYPosition - 5)
    .attr("opacity", 0);

  // Merge entering and updating segments
  const segmentGroupsMerge = segmentGroupsEnter.merge(segmentGroups);

  // Update positions and sizes of rectangles
  segmentGroupsMerge
    .select(".segment")
    .transition()
    .duration(750)
    .attr("x", d => x(d.startValue))
    .attr("width", d => x(d.endValue) - x(d.startValue))
    .attr("fill", d => d3.schemeTableau10[d.i % 10]);

  // Update positions and text of labels
  segmentGroupsMerge
    .select(".segment-label")
    .transition()
    .duration(750)
    .attr("x", d => x((d.startValue + d.endValue) / 2))
    .text(d => d.name);

  // Add hover interactions
  segmentGroupsMerge
    .select(".segment")
    .on("mouseover", function (event, d) {
      d3.select(this.parentNode).select(".segment-label").attr("opacity", 1);
    })
    .on("mouseout", function (event, d) {
      d3.select(this.parentNode).select(".segment-label").attr("opacity", 0);
    });
}

/**
 * Setup modal dialog for editing slider ranges
 */
function setupRangeEditModal(): void {
  const modal = document.getElementById("rangeModal");
  const form = document.getElementById("rangeForm");
  const currentSliderId = document.getElementById("currentSliderId");
  const modalTitle = document.getElementById("modalTitle");
  setupModalFormSubmission(form, currentSliderId);
  setupEditButtons(form, modalTitle, currentSliderId, modal);
}

/**
 * Setup modal form submission
 */
function setupModalFormSubmission(form: HTMLFormElement, currentSliderId: HTMLInputElement): void {
  form.addEventListener("submit", (event: SubmitEvent) => {
    if (event.submitter?.name !== "save") return; // Only make changes if "save" button is clicked
    const formData = new FormData(form);
    const newMin = Number(formData.get("minVal"));
    const newMax = Number(formData.get("maxVal"));
    // Validate input
    if (newMin >= newMax) {
      alert("Minimum value must be less than maximum value");
      return;
    }
    const sliderId = currentSliderId.value;
    updateSliderRange(sliderId, newMin, newMax); // Update the slider with new values
  });
}

/**
 * Setup click handlers for all "Edit Range" buttons
 */
function setupEditButtons(
  form: HTMLFormElement,
  modalTitle: HTMLElement,
  currentSliderId: HTMLInputElement,
  modal: HTMLDialogElement
): void {
  document.querySelectorAll(".range-edit-btn").forEach(button => {
    button.addEventListener("click", () => {
      const sliderId = button.dataset.sliderId;
      const sliderName = button.dataset.sliderName;
      const sliderUnit = button.dataset.sliderUnit;
      const sliderContainer = document.getElementById(sliderId);
      if (!sliderContainer) return;
      modalTitle.textContent = `Edit Range: ${sliderName} (${sliderUnit})`; // Set modal title
      currentSliderId.value = sliderId; // Set current slider ID
      // Set current min/max values
      form.elements.minVal.value = sliderContainer.dataset.min;
      form.elements.maxVal.value = sliderContainer.dataset.max;
      modal.showModal(); // Show the modal
    });
  });
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initializeSliders();
  setupRangeEditModal();
});
