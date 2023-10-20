import React from "react";
import useLTIContext from "../../hooks/useLTIContext";
import { BreadCrumb } from "../BreadCrumb";
import { Logo } from "../Logo";
import { LoadingBarWrapper as LoadingBar } from "../LoadingBarWrapper";

/**
 * Header Component
 *
 * The Header component displays the top header section of the application.
 * It includes the Warren logo, a title, breadcrumb navigation and a loading
 * bar that indicates data fetching status.
 *
 * @component
 * @return {JSX.Element} The rendered Header component
 */
export const Header: React.FC = () => {
  const { appData } = useLTIContext();
  return (
    <>
      <header className="c__header">
        <div className="c__header__logo-title">
          <Logo />
          <h1>Warren</h1>
        </div>
        <BreadCrumb courseInfo={appData.course_info} />
      </header>
      <LoadingBar />
    </>
  );
};
