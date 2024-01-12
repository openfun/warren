import React from "react";
import { Select, Button } from "@openfun/cunningham-react";
import { useLTIContext } from "../../../hooks";

export interface SelectContentProps {
  routes: string[];
}

/**
 * SelectContent component represents a form for selecting content in Deep Linking.
 *
 * @component
 * @param {object} props - The properties of the SelectContent component.
 * @param {string[]} props.routes - An array of strings representing available routes for selection.
 * @returns {JSX.Element} - The JSX element representing the content selection form.
 */
export const SelectContent: React.FC<SelectContentProps> = ({
  routes,
}: SelectContentProps) => {
  const { appData } = useLTIContext();

  return (
    <form
      className="c__select-content--form"
      action={appData.lti_select_form_action_url}
      method="POST"
      aria-label="select"
    >
      <input
        type="hidden"
        name="lti_select_form_jwt"
        value={appData.lti_select_form_jwt}
      />
      <Select
        name="selection"
        label="Selected view"
        defaultValue="demo"
        options={routes.map((route) => ({
          value: route,
          label: route,
        }))}
      />
      <Button type="submit" size="small" fullWidth>
        Submit
      </Button>
    </form>
  );
};
