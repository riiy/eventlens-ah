import { useQuery } from "@tanstack/react-query";
import { fetchAssets, fetchAsset, fetchAssetEvents } from "@/api/assets";

export function useAssets(params?: { market?: string; sector?: string }) {
  return useQuery({
    queryKey: ["assets", params],
    queryFn: () => fetchAssets(params),
  });
}

export function useAsset(id: string | undefined) {
  return useQuery({
    queryKey: ["asset", id],
    queryFn: () => fetchAsset(id!),
    enabled: !!id,
  });
}

export function useAssetEvents(id: string | undefined) {
  return useQuery({
    queryKey: ["asset-events", id],
    queryFn: () => fetchAssetEvents(id!),
    enabled: !!id,
  });
}