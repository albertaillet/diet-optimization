/** @jsx h */
import { h } from './framework';
import { makePie } from "./pie";

function ResultRow({ id, product_code, product_name, ciqual_code, ciqual_name, location_osm_id, location, quantity_g, price }) {
  return (
    <tr>
      <td>
        <a href={`https://world.openfoodfacts.org/product/${product_code}`} target="_blank" style={{ color: 'black' }}>
          {product_name}
        </a>
      </td>
      <td>
        <a href={`https://ciqual.anses.fr/#/aliments/${ciqual_code}`} target="_blank" style={{ color: 'black' }}>
          {ciqual_name}
        </a>
      </td>
      <td>
        <a href={`https://www.openstreetmap.org/way/${location_osm_id}`} target="_blank" style={{ color: 'black' }}>
          {location}
        </a>
      </td>
      <td>
        <a href={`info/${id}`} target="_blank" style={{ color: 'black' }}>
          {quantity_g}
        </a>
      </td>
      <td>
        <a href={`https://prices.openfoodfacts.org/prices/${id}`} target="_blank" className="price-highlight">
          {price}
        </a>
      </td>
    </tr>
  );
}

export function ResultTable(data, result, currency) {
  // If there is no data, display a message.
  if (data.length === 0) {
    return (
      <div style={{ marginTop: '1rem' }}>
        <h2>No solution found. Please try again with different constraints.</h2>
      </div>
    );
  }

  // Compute macronutrient totals.
  const totalProtein = data.reduce((acc, p) => acc + Number(p.protein || 0), 0);
  const totalCarbs = data.reduce((acc, p) => acc + Number(p.carbohydrate || 0), 0);
  const totalFat = data.reduce((acc, p) => acc + Number(p.fat || 0), 0);
  const totalCalories = (totalProtein * 4 + totalCarbs * 4 + totalFat * 9).toFixed(1);
  const proteinPercentage = totalCalories > 0 ? ((totalProtein * 4 / totalCalories) * 100).toFixed(1) : '0';
  const carbsPercentage = totalCalories > 0 ? ((totalCarbs * 4 / totalCalories) * 100).toFixed(1) : '0';
  const fatPercentage = totalCalories > 0 ? ((totalFat * 9 / totalCalories) * 100).toFixed(1) : '0';

  // Render the macronutrient info if available.
  let macroInfo = null;
  if (data[0].hasOwnProperty('protein') && data[0].hasOwnProperty('carbohydrate') && data[0].hasOwnProperty('fat')) {
    macroInfo = (
      <div style={{ display: 'flex', alignItems: 'center', flexDirection: 'row', marginBottom: '0.5rem' }}>
        <div style={{ flex: '0 0 150px' }}>
          <div id="pie"></div>
        </div>
        <div style={{ flex: 1, paddingLeft: '1rem' }}>
          <h3 style={{ marginTop: 0 }}>Macronutrient Distribution</h3>
          <p style={{ margin: 0, fontSize: '0.85rem' }}>
            Protein: {totalProtein.toFixed(1)}g, Carbs: {totalCarbs.toFixed(1)}g, Fat: {totalFat.toFixed(1)}g
          </p>
          <p style={{ margin: 0, fontSize: '0.85rem' }}>Energy: {totalCalories} kcal</p>
          <p style={{ margin: 0, fontSize: '0.85rem' }}>
            Protein: {proteinPercentage}%, Carbs: {carbsPercentage}%, Fat: {fatPercentage}%
          </p>
        </div>
      </div>
    );
  }

  // Build the complete table.
  const table = (
    <div>
      <div className="price-card">
        <h3>
          Total price per day: <span className="price-highlight">{result} {currency}</span>
        </h3>
      </div>
      {macroInfo}
      <h3>Optimized Food Items</h3>
      <div className="table-responsive">
        <table>
          <colgroup>
            <col style={{ width: '25%' }} />
            <col style={{ width: '25%' }} />
            <col style={{ width: '20%' }} />
            <col style={{ width: '15%' }} />
            <col style={{ width: '15%' }} />
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
            {data.map(product => <ResultRow key={product.id} {...product} />)}
          </tbody>
        </table>
      </div>
    </div>
  );

  // After the table is mounted, schedule the pie chart drawing.
  setTimeout(() => {
    const pieElem = document.getElementById('pie');
    if (pieElem) {
      makePie(
        pieElem,
        [totalProtein.toFixed(1), totalCarbs.toFixed(1), totalFat.toFixed(1)],
        ['Protein', 'Carbs', 'Fat'],
        totalCalories
      );
    }
  }, 0);

  return table;
}

export function updateResultTable(products) {
  const resultDiv = document.getElementById('result');
  // Calculate the total price per day.
  const totalPrice = products.reduce((acc, p) => acc + Number(p.price), 0).toFixed(2);
  // Get the currency from the input.
  const currency = document.getElementById('currency').value;
  // Render the ResultTable component into the target element.
  const tableComponent = ResultTable(products, totalPrice, currency);
  resultDiv.innerHTML = '';
  resultDiv.appendChild(tableComponent);
}
