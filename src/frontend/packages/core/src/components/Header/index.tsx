import React from "react";
import { useLTIContext } from "../../hooks";
import { BreadCrumb } from "../BreadCrumb";
import { Logo } from "../Logo";
import { LoadingBarWrapper as LoadingBar } from "../LoadingBarWrapper";

export interface HeaderProps {
  title?: string;
  breadCrumb?: boolean;
}

/**
 * Header Component
 *
 * The Header component displays the top header section of the application.
 * By default, it includes the Warren logo, a title, breadcrumb navigation and a loading
 * bar that indicates data fetching status.
 *
 * @component
 * @param {object} props - The properties of the Header component.
 * @param {string} [props.title] - The title to be displayed in the header.
 * @param {boolean} [props.breadCrumb=true] - A boolean flag indicating whether to display breadcrumb navigation.
 * @returns {JSX.Element} - The rendered Header component with optional title and breadcrumb.
 */
export const Header: React.FC = ({ title, breadCrumb = true }: HeaderProps) => {
  const { appData } = useLTIContext();
  return (
    <>
      <header className="c__header">
        <div className="c__header__logo-title">
          <Logo />
          <h1>{title || "Warren"}</h1>
        </div>
        {breadCrumb && <BreadCrumb courseInfo={appData.course_info} />}
      </header>
      <LoadingBar />
    </>
  );
};
