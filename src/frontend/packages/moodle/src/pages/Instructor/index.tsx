import { ModnameFiltersProvider, ResourceFiltersProvider } from "../../contexts";
import { ModnameFilters, ResourceFilters, ResourcesData } from "../../components";
import { apiAxios, Flexgrid, getCourseContent } from "@openfun/warren-core";
import { useTokenInterceptor, useJwtContext } from "@openfun/warren-core";
/**
 * A React component responsible for rendering a dashboard overview of document statistics.
 *
 * This component combines the Filters component for selecting date ranges and documents, with the DailyDownloads component
 * to display daily document statistics. It serves as a dashboard overview of all documents' statistical data.
 *
 * @returns {JSX.Element} The JSX for the documents statistics overview dashboard.
 */

export default () => {
  const client = useTokenInterceptor(apiAxios);
  console.log("before getContent");
  async function fetchExperiences() {
    const { decodedJwt } = useJwtContext();

    if (!decodedJwt.course_id) {
      throw new Error("Unable to find `course_id` in the LTI context.");
    }
    try {
      
      const experiences = await getCourseContent(client, decodedJwt.course_id);
      console.log('Experiences:', experiences);
    } catch (error) {
      console.error('Error fetching experiences:', error);
    }
  }
  fetchExperiences();

  return (
    <div className="c__overview">
      <ModnameFiltersProvider>
        <ModnameFilters label="select Modnames"/>
        <ResourceFilters/>
          <ResourceFiltersProvider>
            <Flexgrid>
              <ResourcesData />
            </Flexgrid>
          </ResourceFiltersProvider>
      </ModnameFiltersProvider>
    </div>
  );
};
