import React from 'react';
import { AxiosInstance } from "axios";
import { decodeJwtLTI } from '../utils';

// Define the interface for the experience object
interface ExperienceReadSnapshot {
  id: string;
  title: string;
  description: string;
  structure?: string;
  aggregation_level?: string;
  technical_datatypes?: string[];
  iri?: string;
}

/**
 * Retrieves experiences data for the current course.
 *
 * @param {AxiosInstance} client - Axios instance for making the API request.
 * @returns {Promise<ExperienceReadSnapshot[]>} A promise that resolves to the course experiences.
 */
export const getCourseContent = async (
  client: AxiosInstance,
  courseId: string
): Promise<ExperienceReadSnapshot[]> => {
  console.log("before");
  const response = await client.get<ExperienceReadSnapshot[]>(`xi/experiences/${courseId}`);
  return response.data; // Return the data directly, which matches the type.
};
