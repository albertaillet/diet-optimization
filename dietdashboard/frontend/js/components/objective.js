import * as d3 from "../d3";
// import { handleStateChange } from "../index";

const template = `
<h3>Objective function to minimize</h3>
The objective function defines the goal of the optimization. It can be set to "price" to minimize the cost of the diet, or "carbon" to minimize the carbon footprint.
<input style="width: 100%;" type="text" required></input>
`;

/**
 * @param {d3.Selection} parent
 * @param {State} state
 */
export function Objective(parent, state) {
  parent
    .html(template)
    .select("input")
    .attr("value", state.objective || "price") // Set the initial value from state or default to "price"
    .on("input", event => {
      const objective = event.target.value.trim(); // Get the value of the input field
      if (!objective) return; // Do not update if the input is empty
      state.objective = objective; // Update the state with the new objective
      console.log("State updated with objective:", state.objective);
      // handleStateChange();
    });
}
