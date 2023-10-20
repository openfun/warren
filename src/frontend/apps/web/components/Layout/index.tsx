import type { ReactNode } from "react";

import { Header } from "ui/components/Header";
import Footer from "../Footer";

type Props = {
  children: ReactNode;
};

export default ({ children }: Props) => (
  <>
    <Header />
    <main>{children}</main>
    <Footer />
  </>
);
