import { html, render } from 'https://esm.run/lit-html@1';
import { makePie } from './pie.js';

export function updateResultTable(products) {
    const resultDiv = document.getElementById('result');
    const total_price = products.reduce((acc, p) => acc + Number(p.price), 0).toFixed(2);
    const currency = document.getElementById('currency').value;
    const totalProtein = products.reduce((acc, p) => acc + Number(p.protein || 0), 0).toFixed(1);
    const totalCarbs = products.reduce((acc, p) => acc + Number(p.carbohydrate || 0), 0).toFixed(1);
    const totalFat = products.reduce((acc, p) => acc + Number(p.fat || 0), 0).toFixed(1);
    const totalCalories = (totalProtein * 4 + totalCarbs * 4 + totalFat * 9).toFixed(1);
    // const totalCaloriess = products.reduce((acc, p) => acc + Number(p.energy_fibre_kcal || 0), 0).toFixed(1);
    const percentageProtein = (totalProtein * 4 / totalCalories * 100).toFixed(1);
    const percentageCarbs = (totalCarbs * 4 / totalCalories * 100).toFixed(1);
    const percentageFat = (totalFat * 9 / totalCalories * 100).toFixed(1);
    const data = [totalProtein, totalCarbs, totalFat];
    const labels = ['Protein', 'Carbs', 'Fat'];


    // Calculate macronutrient distribution if available
    let macroInfo = '';
    if (products.length === 0) {
        macroInfo = html`
            <div style="margin-top: 1rem;">
                <h2>No solution found. Please try again with different constraints.</h2>
            </div>
        `;
        render(macroInfo, resultDiv);
        return;
    }

    if (products[0].hasOwnProperty('protein') &&
        products[0].hasOwnProperty('fat') &&
        products[0].hasOwnProperty('carbohydrate')) {

        // Create container for pie chart - now more compact
        macroInfo = html`
            <div style="display: flex; align-items: center; flex-direction: row; margin-bottom: 0.5rem;">
                <div style="flex: 0 0 150px;">
                    <div id="pie"></div>
                </div>
                <div style="flex: 1; padding-left: 1rem;">
                    <h3 style="margin-top: 0;">Macronutrient Distribution</h3>
                    <p style="margin: 0; font-size: 0.85rem;">
                        Protein: ${totalProtein}g, Carbs: ${totalCarbs}g, Fat: ${totalFat}g
                    </p>
                    <p style="margin: 0; font-size: 0.85rem;">
                        Energy: ${totalCalories} kcal
                    </p>
                    <p style="margin: 0; font-size: 0.85rem;">
                        Protein: ${percentageProtein}%, Carbs: ${percentageCarbs}%, Fat: ${percentageFat}%
                    </p>
                </div>
            </div>
        `;
    }

    const resultTemplate = html`
        <div class="price-card">
            <h3>Total price per day: <span class="price-highlight">${total_price} ${currency}</span></h3>
        </div>
        ${macroInfo}
        <h3>Optimized Food Items</h3>
        <div class="table-responsive">
            <table>
                <colgroup>
                    <col style="width: 25%;">
                    <col style="width: 25%;">
                    <col style="width: 20%;">
                    <col style="width: 15%;">
                    <col style="width: 15%;">
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
                    ${products.map(product => html`
                        <tr>
                            <td>
                                <a href="https://world.openfoodfacts.org/product/${product.product_code}"
                                   target="_blank">
                                    ${product.product_name}
                                </a>
                            </td>
                            <td>
                                <a href="https://ciqual.anses.fr/#/aliments/${product.ciqual_code}"
                                   target="_blank">
                                    ${product.ciqual_name}
                                </a>
                            </td>
                            <td>
                                <a href="https://www.openstreetmap.org/way/${product.location_osm_id}"
                                   target="_blank">
                                    ${product.location}
                                </a>
                            </td>
                            <td>
                                <a href="info/${product.id}"
                                   target="_blank">
                                    ${product.quantity_g}
                                </a>
                            </td>
                            <td>
                                <a href="https://prices.openfoodfacts.org/prices/${product.id}"
                                   target="_blank" class="price-highlight">
                                    ${product.price}
                                </a>
                            </td>
                        </tr>
                    `)}
                </tbody>
            </table>
        </div>
    `;
    render(resultTemplate, resultDiv);
    makePie(document.getElementById('pie'), data, labels, totalCalories);
}
