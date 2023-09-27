import React from "react";

export type TooltipProps = {
  text: string;
};

/**
 * A React component that displays a tooltip with the provided text.
 *
 * For now, the tooltip position is fixed and always displayed at the top of the component.
 *
 * @param {TooltipProps} props - The component's props.
 * @returns {JSX.Element} The JSX for the Tooltip component.
 */
// FIXME - Dynamically adjust the tooltip position based on content and viewport.
export const Tooltip: React.FC<TooltipProps> = ({ text }) => (
  <div className="c__tooltip">
    <div className="c__tooltip__icon" data-tooltip={text}>
      <span className="material-icons">info_outlined</span>
    </div>
  </div>
);
