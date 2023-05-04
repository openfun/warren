/**
 * @jest-environment jsdom
 */

import React from "react";
import { render, renderHook, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/extend-expect";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { DateContext } from "../DateContext";

import { Total } from "./Total";
import { getVideoViews } from "./fetchVideoViews";

jest.mock("./fetchVideoViews", () => ({
  getVideoViews: jest.fn(),
}));

interface ApiResponse {
  total: number;
  daily_views: Array<{ day: string; views: number }>;
}

interface ApiResult {
  [key: string]: ApiResponse;
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 0,
      cacheTime: 0,
    },
  },
});

const Wrapper: React.FC<React.PropsWithChildren<{}>> = ({ children }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe("Total component", () => {
  const videoIds = [
    "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50",
    "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d",
  ];

  const apiResult: ApiResult = {
    "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50": {
      total: 13,
      daily_views: [
        { day: "2023-04-18", views: 1 },
        { day: "2023-04-19", views: 4 },
        { day: "2023-04-20", views: 8 },
      ],
    },
    "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d": {
      total: 6,
      daily_views: [
        { day: "2023-04-18", views: 1 },
        { day: "2023-04-19", views: 2 },
        { day: "2023-04-20", views: 3 },
      ],
    },
  };

  const since = new Date("2023-04-01");
  const until = new Date("2023-04-10");

  (getVideoViews as jest.Mock).mockImplementation(
    (vid: string, since: Date, until: Date) => {
      return Promise.resolve(apiResult[vid]);
    }
  );

  it("should renders without throwing an error", () => {
    render(
      <DateContext.Provider value={{ since, until }}>
        <Total videoIds={videoIds} />
      </DateContext.Provider>,
      { wrapper: Wrapper }
    );
  });

  it("should contain text and calculate total views correctly", async () => {
    render(
      <DateContext.Provider value={{ since, until }}>
        <Total videoIds={videoIds} />
      </DateContext.Provider>,
      { wrapper: Wrapper }
    );

    await waitFor(() => {
      expect(screen.getByText("19 views in total")).toBeInTheDocument();
    });
  });
});
