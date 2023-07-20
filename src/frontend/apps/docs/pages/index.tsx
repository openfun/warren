import { DailyViews } from "ui";
import AppProvider from "ui/provider/app";
import Filters from "ui/components/filters";

export default function Docs() {
  return (
    <AppProvider>
      <h1>Docs</h1>
      <Filters />
      <DailyViews />
    </AppProvider>
  );
}
