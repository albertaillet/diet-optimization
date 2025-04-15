/** @jsx h */
import { h } from "./framework";
import { makePie } from "./pie";

interface ResultProduct {
  id: string;
  product_code: string;
  product_name: string;
  ciqual_code: string;
  ciqual_name: string;
  location_osm_id: string;
  location: string;
  quantity_g: number;
  price: number;
  protein?: number;
  carbohydrate?: number;
  fat?: number;
}

function ResultRow(row: ResultProduct) {
  // prettier-ignore
  return (
    <tr>
      <td><a href={`https://world.openfoodfacts.org/product/${row.product_code}`} target="_blank" >{row.product_name}</a></td>
      <td><a href={`https://ciqual.anses.fr/#/aliments/${row.ciqual_code}`} target="_blank" >{row.ciqual_name}</a></td>
      <td><a href={`https://www.openstreetmap.org/way/${row.location_osm_id}`} target="_blank" >{row.location}</a></td>
      <td><a href={`info/${row.id}`} target="_blank" >{row.quantity_g}</a></td>
      <td><a href={`https://prices.openfoodfacts.org/prices/${row.id}`} target="_blank">{row.price}</a></td>
    </tr>
  );
}

export function ResultTable(data: ResultProduct[], result: number, currency: string): HTMLElement {
  if (data.length === 0) {
    return (
      <div style={{ marginTop: "1rem" }}>
        <h2>No solution found. Please try again with different constraints.</h2>
      </div>
    );
  }

  const totalProtein = data.reduce((acc, p) => acc + Number(p.protein || 0), 0);
  const totalCarbs = data.reduce((acc, p) => acc + Number(p.carbohydrate || 0), 0);
  const totalFat = data.reduce((acc, p) => acc + Number(p.fat || 0), 0);
  const totalCalories = totalProtein * 4 + totalCarbs * 4 + totalFat * 9;
  const proteinPercentage = totalCalories > 0 ? (((totalProtein * 4) / totalCalories) * 100).toFixed(1) : "0";
  const carbsPercentage = totalCalories > 0 ? (((totalCarbs * 4) / totalCalories) * 100).toFixed(1) : "0";
  const fatPercentage = totalCalories > 0 ? (((totalFat * 9) / totalCalories) * 100).toFixed(1) : "0";

  let macroInfo = null;
  if (data[0].hasOwnProperty("protein") && data[0].hasOwnProperty("carbohydrate") && data[0].hasOwnProperty("fat")) {
    macroInfo = (
      <div style={{ display: "flex", alignItems: "center", flexDirection: "row", marginBottom: "0.5rem" }}>
        <div style={{ flex: "0 0 150px" }}>
          <div id="pie"></div>
        </div>
        <div style={{ flex: 1, paddingLeft: "1rem" }}>
          <h3 style={{ marginTop: 0 }}>Macronutrient Distribution</h3>
          <p style={{ margin: 0, fontSize: "0.85rem" }}>
            Protein: {totalProtein.toFixed(1)}g, Carbs: {totalCarbs.toFixed(1)}g, Fat: {totalFat.toFixed(1)}g
          </p>
          <p style={{ margin: 0, fontSize: "0.85rem" }}>Energy: {totalCalories.toFixed(1)} kcal</p>
          <p style={{ margin: 0, fontSize: "0.85rem" }}>
            Protein: {proteinPercentage}%, Carbs: {carbsPercentage}%, Fat: {fatPercentage}%
          </p>
        </div>
      </div>
    );
  }
  // prettier-ignore
  const table = (
    <div>
      <div>
        <h3>
          Total price per day: <span>{result} {currency}</span>
        </h3>
      </div>
      {macroInfo}
      <h3>Optimized Food Items</h3>
      <div>
        <table>
          <colgroup>
            <col style={{ width: "25%" }} />
            <col style={{ width: "25%" }} />
            <col style={{ width: "20%" }} />
            <col style={{ width: "15%" }} />
            <col style={{ width: "15%" }} />
          </colgroup>
          <thead>
            <tr>
              <th>Product name</th>
              <th>Ciqual Name</th>
              <th>Location</th>
              <th>Quantity (g)</th>
              <th>Price</th>
            </tr>
          </thead>
          <tbody>
            {data.map(product => (<ResultRow {...product} />))}
          </tbody>
        </table>
      </div>
    </div>
  );

  setTimeout(() => {
    const pieElem = document.getElementById("pie");
    if (!pieElem) return;
    makePie(pieElem, [totalProtein, totalCarbs, totalFat], ["Protein", "Carbs", "Fat"], totalCalories);
  }, 0);

  return table;
}

export function updateResultTable(products) {
  const resultDiv = document.getElementById("result");
  const totalPrice = products.reduce((acc, p) => acc + Number(p.price), 0).toFixed(2);
  const currency = document.getElementById("currency").value;
  const tableComponent = ResultTable(products, totalPrice, currency);
  resultDiv.innerHTML = tableComponent.innerHTML;
}
