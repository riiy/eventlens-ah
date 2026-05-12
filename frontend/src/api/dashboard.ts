import { apiClient } from "./client";
import type { DashboardSummary, TopEventItem, RecentDocumentItem } from "@/types/dashboard";

export const fetchDashboardSummary = () =>
  apiClient.get<DashboardSummary>("/dashboard/summary");

export const fetchTopEvents = (limit = 10) =>
  apiClient.get<TopEventItem[]>("/dashboard/top-events", { limit });

export const fetchRecentDocuments = (limit = 10) =>
  apiClient.get<RecentDocumentItem[]>("/dashboard/recent-documents", { limit });