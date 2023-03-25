import type { ReactNode } from "react";

import Header from "./Header";
import Footer from "./Footer";

type Props = {
  children: ReactNode;
};

export default function Layout({ children }: Props) {
  return (
    <>
      <Header />
      <main>{children}</main>
      <Footer />
    </>
  );
}
