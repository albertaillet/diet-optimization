/** Global state
 * @typedef {'energy' | 'macro' | 'sugar' | 'fatty_acid' | 'mineral' | 'vitamin' | 'other'} NutrientType
 *
 * @typedef {Object} InputTabs
 * @property {string} current - The current active tab.
 *
 * @typedef {Object} Slider
 * @property {string} id
 * @property {string} name
 * @property {string} unit
 * @property {NutrientType} nutrient_type
 * @property {number} min
 * @property {number} max
 * @property {number} lower
 * @property {number} upper
 * @property {boolean} active - Indicates if the slider is active.
 *
 * @typedef {Object} Result
 * @property {string} id
 * @property {string} product_code
 * @property {string} product_name
 * @property {string} ciqual_name
 * @property {string} ciqual_code
 * @property {string} location
 * @property {string} location_osm_id
 * @property {number} quantity_g
 * @property {number} price
 * Then it also has one property for each nutrient type, e.g. energy, macro, sugar, etc.
 *
 * @typedef {Object} MapTransform
 * @property {number} x - x translation.
 * @property {number} y - y translation.
 * @property {number} k - Zoom scale factor.
 *
 * @typedef {Object} State
 * @property {string} currency - Current currency.
 * @property {Array<Slider>} sliders - Current sliders (active and inactive).
 * @property {MapTransform} mapTransform
 * @property {Array<Object>} locations - Currently selected locations. Has location IDs as keys.
 * @property {Array<Result>} resultData - Reslut data from the optimization.
 * @property {InputTabs} inputTabs - Current input tab state.
 * @property {string|null} brushMode - Current brush mode.
 *
 * id,lat,lon,name,count
 * @typedef {Object} LocationInfo
 * @property {string} id
 * @property {number} lat - Latitude.
 * @property {number} lon - Longitude.
 * @property {string} name
 * @property {number} count
 * @property {number} x - Projected x coordinate (calculated from lat/lon).
 * @property {number} y - Projected y coordinate (calculated from lat/lon).
 *
 *
 */
