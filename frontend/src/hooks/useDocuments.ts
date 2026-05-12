import { useQuery } from "@tanstack/react-query";
import { fetchDocuments, fetchDocument } from "@/api/rawDocuments";
import type { RawDocumentListParams } from "@/types/rawDocument";

export function useDocuments(params?: RawDocumentListParams) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: () => fetchDocuments(params),
  });
}

export function useDocument(id: string | undefined) {
  return useQuery({
    queryKey: ["document", id],
    queryFn: () => fetchDocument(id!),
    enabled: !!id,
  });
}