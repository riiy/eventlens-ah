import { apiClient } from "./client";
import type { RawDocument, RawDocumentCreate, RawDocumentListParams } from "@/types/rawDocument";
import type { PaginatedResponse } from "@/types/common";

export const fetchDocuments = (params?: RawDocumentListParams) =>
  apiClient.get<PaginatedResponse<RawDocument>>("/raw-documents", params as Record<string, unknown>);

export const fetchDocument = (id: string) =>
  apiClient.get<RawDocument>(`/raw-documents/${id}`);

export const ingestDocument = (data: RawDocumentCreate) =>
  apiClient.post<RawDocument>("/raw-documents", data);