/**
 * Extracts and parses JSON-formatted data embedded within a designated DOM element.
 * The data is expected to be stored as a string within the `data-context` attribute of the element.
 *
 * @throws {Error} If the DOM element with id `warren-frontend-data` is not found.
 * @throws {Error} If the `data-context` attribute is missing from the identified element.
 * @throws {SyntaxError|TypeError} If errors occur during JSON parsing.
 *
 * @returns {any} Parsed JavaScript object representing the extracted data.
 */
export const parseDataContext = (): any => {
  const element = document.getElementById("warren-frontend-data");

  if (!element) {
    throw new Error("`warren-frontend-data` is missing from DOM.");
  }

  const dataString = element.getAttribute("data-context");

  if (!dataString) {
    throw new Error("`app_data` is missing from DOM.");
  }

  // Sanitize the data string to match JSON requirements.
  const dataStringSanitized = dataString.replaceAll("'", '"');
  return JSON.parse(dataStringSanitized);
};
