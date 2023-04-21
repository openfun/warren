import { createContext } from 'react';

type DateContext = {
    since: number,
    until: number,
}
export const DateContext = createContext({since:0, until:9999999999999});