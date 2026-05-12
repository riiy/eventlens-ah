import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchEvents,
  fetchEvent,
  extractEvents,
  generateHypothesis,
  scoreEvent,
  fetchEventAssets,
  fetchEventHypotheses,
  fetchEventPriceReactions,
} from "@/api/events";
import type { MarketEventListParams } from "@/types/marketEvent";

export function useEvents(params?: MarketEventListParams) {
  return useQuery({
    queryKey: ["events", params],
    queryFn: () => fetchEvents(params),
  });
}

export function useEvent(id: string | undefined) {
  return useQuery({
    queryKey: ["event", id],
    queryFn: () => fetchEvent(id!),
    enabled: !!id,
  });
}

export function useExtractEvents() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: extractEvents,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["events"] }); },
  });
}

export function useGenerateHypothesis() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: generateHypothesis,
    onSuccess: (_data, eventId) => {
      qc.invalidateQueries({ queryKey: ["event", eventId] });
      qc.invalidateQueries({ queryKey: ["event-hypotheses", eventId] });
    },
  });
}

export function useScoreEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: scoreEvent,
    onSuccess: (_data, eventId) => {
      qc.invalidateQueries({ queryKey: ["event", eventId] });
      qc.invalidateQueries({ queryKey: ["events"] });
    },
  });
}

export function useEventAssets(eventId: string | undefined) {
  return useQuery({
    queryKey: ["event-assets", eventId],
    queryFn: () => fetchEventAssets(eventId!),
    enabled: !!eventId,
  });
}

export function useEventHypotheses(eventId: string | undefined) {
  return useQuery({
    queryKey: ["event-hypotheses", eventId],
    queryFn: () => fetchEventHypotheses(eventId!),
    enabled: !!eventId,
  });
}

export function useEventPriceReactions(eventId: string | undefined) {
  return useQuery({
    queryKey: ["event-price-reactions", eventId],
    queryFn: () => fetchEventPriceReactions(eventId!),
    enabled: !!eventId,
  });
}