export interface EventAssetLink {
  id: string;
  event_id: string;
  asset_id: string;
  symbol?: string;
  name?: string;
  impact_direction: string;
  impact_strength: number;
  reason: string;
  confidence_score: number;
  created_at: string;
}