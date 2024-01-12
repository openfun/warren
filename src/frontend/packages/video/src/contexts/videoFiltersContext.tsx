import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";
import { Video } from "../types";

export interface VideoFiltersContextType {
  videos: Array<Video>;
  setVideos: Dispatch<SetStateAction<Array<Video>>>;
}

export const VideoFiltersContext =
  createContext<VideoFiltersContextType | null>(null);

export const VideoFiltersProvider: React.FC<{ children: any }> = ({
  children,
}) => {
  const [videos, setVideos] = useState<Array<Video>>([]);
  const value = useMemo(() => ({ videos, setVideos }), [videos]);

  return (
    <VideoFiltersContext.Provider value={value}>
      {children}
    </VideoFiltersContext.Provider>
  );
};
