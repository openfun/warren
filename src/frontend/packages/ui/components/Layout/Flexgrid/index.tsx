import React from "react";
import type { ReactNode } from "react";

export type FlexgridProps = {
  children: ReactNode;
};

/**
 * Flexgrid Component
 *
 * The Flexgrid component is a wrapper that provides a flex grid layout for its children elements.
 *
 * @component
 * @param {ReactNode} props.children - The children elements to be rendered within the grid.
 * @returns {JSX.Element} The Autogrid component with its children.
 */
export const Flexgrid: React.FC<FlexgridProps> = ({ children }) => (
  <div className="c__flexgrid">{children}</div>
);
