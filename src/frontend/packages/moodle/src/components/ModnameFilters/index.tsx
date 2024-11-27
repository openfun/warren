import React from "react";
import { Select } from "@openfun/cunningham-react";
import { useModnameFilters } from "../../hooks/useModnameFilters";
import { ViewsActivities } from "../../types";

export type ModnameFiltersProps = {
  label: string;
};

const MODNAMES = Object.values(ViewsActivities);

export const ModnameFilters: React.FC<ModnameFiltersProps> = ({ label }) => {
  const { setModnames } = useModnameFilters();

  const getModnameOptions = () => MODNAMES.map((modname) => ({
    value: modname,
    label: modname,
  }));

  const handleModnamesChange = (value: string | number | string[] | undefined) => {
    if (Array.isArray(value)) {
      setModnames(value as ViewsActivities[]);
    }
  };

  return (
    <Select
      label={label}
      defaultValue={MODNAMES[0]}
      options={getModnameOptions()}
      multi={true}
      monoline={true}
      onChange={(event) => handleModnamesChange(event.target.value)}
    />
  );
};
