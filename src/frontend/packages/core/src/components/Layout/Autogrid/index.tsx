import React from "react";
import type { ReactNode } from "react";

export type AutogridProps = {
  children: ReactNode;
};

/**
 * Autogrid Component
 *
 * The Autogrid component is a wrapper that provides a grid layout for its children elements.
 *
 * @component
 * @param {ReactNode} props.children - The children elements to be rendered within the grid.
 * @returns {JSX.Element} The Autogrid component with its children.
 */
export const Autogrid: React.FC<AutogridProps> = ({ children }) => (
  <div className="c__autogrid">{children}</div>
);
