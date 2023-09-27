import React from "react";
import type { ReactNode } from "react";
import { Tooltip } from "../Tooltip";

export type CardProps = {
  children: ReactNode;
  title?: string;
  tooltip?: string;
};

/**
 * A reusable React component for displaying content within a card-like container.
 *
 * This component will be replaced by Cunningham's Card component for additional features.
 *
 * @param {CardProps} props - The component's props.
 * @returns {JSX.Element} The JSX for the Card component.
 */
export const Card: React.FC<CardProps> = ({ children, title, tooltip }) => (
  <div className="c__card">
    {title && (
      <div className="c__card__title">
        <h3>{title}</h3>
        {tooltip && <Tooltip text={tooltip} />}
      </div>
    )}
    <div className="c__card__content">{children}</div>
  </div>
);
