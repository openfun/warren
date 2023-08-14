import React, { useMemo } from "react";
import { parseDataContext } from "ui/utils/parseDataContext";
import useAppData from "ui/hooks/useAppData";
import { DailyViews, Filters } from "ui";

const Plots = {
  Views: DailyViews,
};

const data = parseDataContext();

export const AppInitializer = () => {
  const { setData } = useAppData();
  setData(data);

  // todo : handle jwt

  // todo: check if it's in authorized values
  // todo: else have a default error component

  const Content = useMemo(() => Plots[data.plot_id], [data]);

  return (
    <>
      <Filters />
      <Content />
    </>
  );
};
