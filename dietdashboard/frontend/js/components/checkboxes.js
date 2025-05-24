import { select } from "../d3";
import { handleStateChange } from "../index";

/**
 * @param {d3,Selection} parent
 * @param {object} state
 */
export function NutrientCheckboxes(parent, state) {
  parent
    .append("details")
    .call(details => details.append("summary").text("Select Nutrients"))
    .append("form")
    .attr("method", "dialog")
    .attr("class", "nutrient-selector-form")
    .append("ul")
    .selectAll("li")
    .data([
      { id: "macro", name: "Macronutrients" },
      { id: "micro", name: "Micronutrients" }
    ])
    .join("li")
    .each(function (nutrientType) {
      NurtienCatergoryCheckboxes(
        select(this),
        nutrientType,
        state.sliders.filter(nutrient => nutrient.nutrient_type === nutrientType.id)
      );
    });
}

/**
 * @param {d3,Selection} parent
 * @param {object} state
 */
export function NurtienCatergoryCheckboxes(parent, category, nutrients) {
  const setAll = checked => {
    parent
      .selectAll("input[type='checkbox']")
      .property("checked", checked)
      .each(nutrient => (nutrient.active = checked));
    handleStateChange();
  };
  const selectAll = () => setAll(true);
  const deselectAll = () => setAll(false);

  parent
    .append("li")
    .html(`<div style="display: flex; justify-content: space-between; align-items: center">`)
    .call(div => div.append("h3").text(category.name))
    .call(div => div.append("button").text("Select All").on("click", selectAll))
    .call(div => div.append("button").text("Deselect All").on("click", deselectAll))
    .append("ul")
    .selectAll("li")
    .data(nutrients)
    .join("li")
    .append("label")
    .call(label =>
      label
        .append("input")
        .attr("type", "checkbox")
        .property("checked", nutrient => nutrient.active)
        .on("click", (event, nutrient) => {
          nutrient.active = event.target.checked;
          handleStateChange();
        })
    )
    .append("span")
    .text(nutrient => nutrient.name);
}
