import * as d3 from "../d3";
import { handleStateChange } from "../index";
import { Table } from "./table";

// Regex pattern from objective.py
const template = `
<h3>Objective function to minimize</h3>
The objective function defines the goal of the optimization. It can be set to "price" to minimize the cost of the diet, or "carbon" to minimize the carbon footprint.
<input required type="text" pattern="^[_\w\d+\-*\/%\^&|<>~!@\(\)\.\,\s]+$" style="width: 100%" id="objective"></input>
<style>
#objective:focus { outline: none; }
#objective:valid { border-color: green; }
#objective:invalid { border-color: red; }
#objective.valid { border-color: green; }
#objective.invalid { border-color: red; }
</style>
<br>
<p id="validation-message"></p>
<br>
<p>
You can use any valid Python expression here, such as <code>price</code>, <code>carbon</code>, or a custom expression like <code>price + 0.1 * carbon</code>. The expression can include arithmetic operations, variables, and functions.
</p>
<table>
  <thead>
    <tr>
      <th>Variable</th>
      <th>Description</th>
      <th>Mean</th>
      <th>Min</th>
      <th>Max</th>
    </tr>
  </thead>
  <tbody id="objective-variables"></tbody>
</table>
`;

/**
 * @param {string} objective
 * @param {State} state
 */
function onInputChange(objective, state) {
  const input = d3.select("#objective");
  const validationMessage = d3.select("#validation-message");
  if (!objective) return; // Do not update if the input is empty
  fetch(`/validate_objective?q=${encodeURIComponent(objective)}`)
    .then(response => response.json())
    .then(data => {
      input.classed("valid", data.valid).classed("invalid", !data.valid);
      if (data.valid) {
        state.objective = objective; // Update the state with the new objective
        validationMessage.text("Valid objective function.");
        handleStateChange();
      } else {
        validationMessage.text(data.message);
      }
    });
}

/**
 * @param {d3.Selection} parent
 * @param {State} state
 */
export function Objective(parent, state) {
  parent
    .html(template)
    .select("input")
    .attr("value", state.objective || "price") // Set the initial value from state or default to "price"
    .on("input", event => onInputChange(event.target.value, state));

  // Loading the objective variables table
  parent.select("#objective-variables").html("<tr><td>Loading...</td></tr>");
  fetch("/static/column_description.csv")
    .then(response => response.text())
    .then(text => d3.csvParse(text, d3.autoType))
    .then(csv => csv.map(row => [row.column_name, row.comment, row.mean, row.min, row.max]))
    .then(csv => Table(parent.select("#objective-variables"), csv));

  onInputChange(state.objective, state); // Validate the initial value
}
