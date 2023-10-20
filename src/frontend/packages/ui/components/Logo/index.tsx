import React, { SVGProps } from "react";
import { WARREN_COLOR } from "../../utils";

export interface LogoProps extends SVGProps<SVGElement> {
  color?: string;
}

/**
 * Logo Component
 *
 * The Logo component displays the Warren logo as an SVG element.
 *
 * @component
 * @param {LogoProps} props - The properties for the Logo component.
 * @param {string} props.color - The color of the logo.
 * @param {SVGProps<SVGElement>} props - Additional SVG properties.
 * @return {JSX.Element} The rendered Logo component.
 */
export const Logo: React.FC<LogoProps> = (props) => (
  <svg
    data-name="Logo warren"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 52 52"
    {...props}
  >
    <path
      d="M44.39 7.61C39.68 2.91 33.18 0 26 0S12.32 2.91 7.61 7.61C2.91 12.32 0 18.82 0 26c0 14.36 11.64 26 26 26 7.18 0 13.68-2.91 18.39-7.61S52 33.18 52 26s-2.91-13.68-7.61-18.39Zm-7.14 32.03h-5.69l-5.29-19.86L21 39.64h-5.82L8.83 13.07h5.49l4 18.25 4.86-18.25h6.38l4.66 18.56 4.08-18.56h5.4l-6.45 26.57Z"
      style={{
        fill: props.color || WARREN_COLOR,
        strokeWidth: 0,
      }}
      data-name="Logo"
    />
  </svg>
);
