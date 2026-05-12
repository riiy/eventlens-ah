import { apiClient } from "./client";
import type { DemoIngestionResponse } from "@/types/ingestion";

export const runDemoIngestion = () =>
  apiClient.post<DemoIngestionResponse>("/ingestion/run-demo");