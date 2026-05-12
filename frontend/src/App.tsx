import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider, App as AntApp } from "antd";
import zhCN from "antd/locale/zh_CN";
import AppLayout from "@/components/AppLayout";
import DashboardPage from "@/pages/DashboardPage";
import EventListPage from "@/pages/EventListPage";
import EventDetailPage from "@/pages/EventDetailPage";
import AssetDetailPage from "@/pages/AssetDetailPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

const theme = {
  token: {
    colorPrimary: "#1a365d",
    borderRadius: 6,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={theme} locale={zhCN}>
        <AntApp>
          <BrowserRouter>
            <Routes>
              <Route element={<AppLayout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/events" element={<EventListPage />} />
                <Route path="/events/:eventId" element={<EventDetailPage />} />
                <Route path="/assets" element={<AssetDetailPage />} />
                <Route path="/assets/:assetId" element={<AssetDetailPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}