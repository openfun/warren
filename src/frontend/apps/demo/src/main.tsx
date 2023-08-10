import React from "react";
import { createRoot } from "react-dom/client";
import "./index.scss";
import { App } from "./App";

document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('#warren-frontend-root');

  if (!container) {
    throw new Error('container not found!');
  }

  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
});
