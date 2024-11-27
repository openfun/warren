import React, { useEffect, useState } from "react";
import { useModnameFilters } from "../../hooks/useModnameFilters";
import { MoodleResource } from "../../types";



export const RESOURCES: Array<MoodleResource> = [
    { id: "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50", title: "Resource 1", technical_datatypes: ["mod_assign"] },
    { id: "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d", title: "Resource 2", technical_datatypes: ["mod_assign"] },
    { id: "uuid://541dab6b-50ae-4444-b230-494f0621f132", title: "Resource 3", technical_datatypes: ["mod_assign"] },
    { id: "uuid://69d32ad5-3af5-4160-a995-87e09da6865c", title: "Resource 4", technical_datatypes: ["mod_book"] },
    { id: "uuid://7d4f3c70-1e79-4243-9b7d-166076ce8bfb", title: "Resource 5", technical_datatypes: ["mod_book"] },
    { id: "uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e", title: "Resource 6", technical_datatypes: ["mod_glossary"] },
    { id: "uuid://b172ec09-97ec-4651-bc57-6eabebf47ed0", title: "Resource 7", technical_datatypes: ["mod_survey"] },
    { id: "uuid://d613b564-5d18-4238-a69c-0fc8cee5d0e7", title: "Resource 8", technical_datatypes: ["mod_survey"] },
    { id: "uuid://dd38149d-956a-483d-8975-c1506de1e1a9", title: "Resource 9", technical_datatypes: ["mod_survey"] },
    { id: "uuid://e151ee65-7a72-478c-ac57-8a02f19e748b", title: "Resource 10", technical_datatypes: ["mod_survey"] },
  ];

export const ResourceFilters: React.FC = () => {
  const { selectedModnames } = useModnameFilters();
  const [filteredResources, setFilteredResources] = useState<MoodleResource[]>([]);

  useEffect(() => {
    // Filter resources based on selected modnames
    const newFilteredResources = RESOURCES.filter((resource) =>
      resource.technical_datatypes.some((datatype) =>
        selectedModnames.includes(datatype)
      )
    );
    setFilteredResources(newFilteredResources);
  }, [selectedModnames]);

  return (
    <div>
      <h2>Filtered Resources</h2>
      <ul>
        {filteredResources.map((resource) => (
          <li key={resource.id}>{resource.title}</li>
        ))}
      </ul>
    </div>
  );
};
