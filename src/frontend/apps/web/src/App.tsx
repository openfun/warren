import React from "react";
import AppProvider from "ui/provider/app";
import Filters from "ui/components/filters";
import {DailyViews} from "ui";
import Layout from "../components/Layout";

export const App = () => {
    return (
        <Layout>
            <AppProvider>
                <Filters />
                <DailyViews />
            </AppProvider>
        </Layout>
    )
}
