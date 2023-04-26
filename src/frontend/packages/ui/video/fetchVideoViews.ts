import axios from "axios";

export function getVideoViews(videoId: string, since: Date, until: Date) {
  return axios
    .get(
      `${
        process.env.NEXT_PUBLIC_WARREN_BACKEND_ROOT_URL
      }/api/v1/video/${videoId}/views?since=${since.getTime()}&until=${until.getTime()}`
    )
    .then((res) => res.data);
}
