import React from "react";
import useLTIContext from "ui/hooks/useLTIContext";

import { Select, Button } from "@openfun/cunningham-react";

export default () => {
  const { appData } = useLTIContext();

  return (
    <form
      className="c__select-content--form"
      action={appData.lti_select_form_action_url}
      method="POST"
      aria-label="select"
    >
      {Object.entries(appData.lti_select_form_data).map(([name, value]) => (
        <input key={name} type="hidden" name={name} value={value} />
      ))}
      <Select
        name="selection"
        label="Selected view"
        defaultValue="demo"
        options={[{ value: "demo", label: "demo" }]}
      />
      <Button type="submit" size="small" fullWidth>
        Submit
      </Button>
    </form>
  );
};
