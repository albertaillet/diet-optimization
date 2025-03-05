import { html, render } from 'https://esm.run/lit-html@1';

export function updateResultTable(products) {
    const resultDiv = document.getElementById('result');
    const total_price = products.reduce((acc, p) => acc + Number(p.price), 0).toFixed(2);
    const resultTemplate = html`
        <h3>Total price per day: ${total_price} EUR</h3>
        <table>
            <colgroup>
                <col style="width: 30%;">
                <col style="width: 30%;">
                <col style="width: 20%;">
                <col style="width: 13%;">
                <col style="width: 10%;">
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
                               target="_blank" style="color: black;">
                                ${product.product_name}
                            </a>
                        </td>
                        <td>
                            <a href="https://ciqual.anses.fr/#/aliments/${product.ciqual_code}"
                               target="_blank" style="color: black;">
                                ${product.ciqual_name}
                            </a>
                        </td>
                        <td>
                            <a href="https://www.openstreetmap.org/way/${product.location_osm_id}"
                               target="_blank" style="color: black;">
                                ${product.location}
                            </a>
                        </td>
                        <td>
                            <a href="info/${product.id}"
                               target="_blank" style="color: black;">
                                ${product.quantity_g}
                            </a>
                        </td>
                        <td>
                            <a href="https://prices.openfoodfacts.org/prices/${product.id}"
                               target="_blank" style="color: black;">
                                ${product.price}
                            </a>
                        </td>
                    </tr>
                `)}
            </tbody>
        </table>
    `;
    render(resultTemplate, resultDiv);
}
