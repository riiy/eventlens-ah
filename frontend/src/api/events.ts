import { apiClient } from "./client";
import type { MarketEvent, MarketEventListParams } from "@/types/marketEvent";
import type { PaginatedResponse } from "@/types/common";
import type { EventAssetLink } from "@/types/eventAssetLink";
import type { ResearchHypothesis } from "@/types/researchHypothesis";
import type { EventPriceReaction } from "@/types/eventPriceReaction";

export const fetchEvents = (params?: MarketEventListParams) =>
  apiClient.get<PaginatedResponse<MarketEvent>>("/events", params as Record<string, unknown>);

export const fetchEvent = (id: string) =>
  apiClient.get<MarketEvent>(`/events/${id}`);

export const extractEvents = (documentIds: string[]) =>
  apiClient.post<MarketEvent[]>("/events/extract", { document_ids: documentIds });

export const generateHypothesis = (eventId: string) =>
  apiClient.post<ResearchHypothesis>(`/events/${eventId}/generate-hypothesis`);

export const scoreEvent = (eventId: string) =>
  apiClient.post<MarketEvent>(`/events/${eventId}/score`);

export const fetchEventAssets = (eventId: string) =>
  apiClient.get<EventAssetLink[]>(`/events/${eventId}/assets`);

export const fetchEventHypotheses = (eventId: string) =>
  apiClient.get<ResearchHypothesis[]>(`/events/${eventId}/hypotheses`);

export const fetchEventPriceReactions = (eventId: string) =>
  apiClient.get<EventPriceReaction[]>(`/events/${eventId}/price-reactions`);