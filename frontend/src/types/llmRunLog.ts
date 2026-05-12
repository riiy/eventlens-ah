export interface LLMRunLog {
  id: string;
  task_type: string;
  model_name: string;
  prompt_version: string;
  input_hash: string;
  output_json: Record<string, unknown> | null;
  error_message: string | null;
  latency_ms: number | null;
  success: boolean;
  created_at: string;
}