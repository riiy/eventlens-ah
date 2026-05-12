export interface EventPriceReaction {
  id: string;
  event_id: string;
  asset_id: string;
  return_1d: number | null;
  return_3d: number | null;
  return_5d: number | null;
  return_20d: number | null;
  max_drawdown: number | null;
  volume_change: number | null;
  benchmark_return: number | null;
  excess_return: number | null;
  notes: string | null;
  created_at: string;
}