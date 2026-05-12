import { useQuery } from "@tanstack/react-query";
import { fetchDashboardSummary, fetchTopEvents, fetchRecentDocuments } from "@/api/dashboard";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: fetchDashboardSummary,
    refetchInterval: 30000,
  });
}

export function useTopEvents(limit = 10) {
  return useQuery({
    queryKey: ["dashboard-top-events", limit],
    queryFn: () => fetchTopEvents(limit),
  });
}

export function useRecentDocuments(limit = 10) {
  return useQuery({
    queryKey: ["dashboard-recent-documents", limit],
    queryFn: () => fetchRecentDocuments(limit),
  });
}