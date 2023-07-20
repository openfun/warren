import { DailyViews } from "ui";
import AppProvider from "ui/provider/app";

export default function Docs() {
  return (
    <AppProvider>
      <h1>Docs</h1>
      <DailyViews videoIds={["uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e"]} />
    </AppProvider>
  );
}
