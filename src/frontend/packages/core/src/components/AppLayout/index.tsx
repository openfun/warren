import type { ReactNode } from "react";

import React from "react";
import { Header } from "../Header";
import { Footer } from "../Footer";

export type AppLayoutProps = {
  children: ReactNode;
};

/**
 * AppLayout component defines the layout structure of the application.
 *
 * @component
 * @param {object} props - The properties of the AppLayout component.
 * @param {ReactNode} props.children - The main content to be displayed within the layout.
 * @returns {JSX.Element} - The rendered AppLayout component with header, main content, and footer.
 */
export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
}: AppLayoutProps) => (
  <>
    <Header />
    <main>{children}</main>
    <Footer />
  </>
);
