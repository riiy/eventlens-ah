import { apiClient } from "./client";
import type { Asset, AssetCreate } from "@/types/asset";
import type { MarketEvent } from "@/types/marketEvent";
import type { PaginatedResponse } from "@/types/common";

export const fetchAssets = (params?: { market?: string; sector?: string }) =>
  apiClient.get<PaginatedResponse<Asset>>("/assets", params as Record<string, unknown>);

export const fetchAsset = (id: string) =>
  apiClient.get<Asset>(`/assets/${id}`);

export const fetchAssetEvents = (id: string) =>
  apiClient.get<MarketEvent[]>(`/assets/${id}/events`);

export const createAsset = (data: AssetCreate) =>
  apiClient.post<Asset>("/assets", data);