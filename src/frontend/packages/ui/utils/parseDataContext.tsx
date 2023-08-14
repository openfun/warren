export const parseDataContext = (): any => {
  const element = document.getElementById("warren-frontend-data");

  if (!element) {
    throw new Error("`warren-frontend-data` is missing from DOM.");
  }

  const dataString = element.getAttribute("data-context");

  if (!dataString) {
    throw new Error("`app_data` is missing from DOM.");
  }

  const dataStringSanitized = dataString.replaceAll("'", '"');
  return JSON.parse(dataStringSanitized);
};
