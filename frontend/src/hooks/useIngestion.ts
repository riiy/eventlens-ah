import { useMutation, useQueryClient } from "@tanstack/react-query";
import { runDemoIngestion } from "@/api/ingestion";

export function useRunDemoIngestion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: runDemoIngestion,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
      qc.invalidateQueries({ queryKey: ["events"] });
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}