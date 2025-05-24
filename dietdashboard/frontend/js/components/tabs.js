import { persistState } from "..";
/**
 *
 * @param {d3.Selection} parent
 * @param {Array} tabs - [{ id: string, name: string, component: function }]
 * @param {object} tabState - The state object to be passed to the component function
 */
export function Tabs(parent, tabs, tabState) {
  const tabSelection = parent
    .append("div")
    .attr("class", "tabs-buttons")
    .selectAll("button")
    .data(tabs)
    .join(enter =>
      enter
        .append("button")
        .attr("class", "tab-button")
        .classed("active", d => d.id === tabState.currentTab)
        .text(d => d.name)
    );
  const tabContent = parent.append("div").attr("class", "tab-content");
  tabSelection.on("click", (event, d) => {
    parent.selectAll("button.tab-button").classed("active", false);
    tabState.currentTab = d.id;
    persistState();
    d.component(tabContent);
    event.target.classList.add("active");
  });

  // Set the initial tab
  const initialTab = tabs.find(tab => tab.id === tabState.currentTab);
  tabContent.call(initialTab.component, [tabContent]);
}
