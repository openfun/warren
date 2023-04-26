import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { DailyViewsAreaGraph } from "ui";

const queryClient = new QueryClient();
export default function Docs() {
  return (
    <QueryClientProvider client={queryClient}>
      <h1>Docs</h1>
      <DailyViewsAreaGraph
        videoIds={["uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e"]}
      />
    </QueryClientProvider>
  );
}
