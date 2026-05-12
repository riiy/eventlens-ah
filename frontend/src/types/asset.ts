export interface Asset {
  id: string;
  symbol: string;
  name: string;
  market: "A_SHARE" | "HK_SHARE";
  exchange: string;
  sector: string | null;
  industry: string | null;
  business_tags: string[];
  liquidity_score: number;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface AssetCreate {
  symbol: string;
  name: string;
  market: string;
  exchange: string;
  sector?: string;
  industry?: string;
  business_tags?: string[];
}