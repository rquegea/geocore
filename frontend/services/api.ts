import { VisibilityData, Competitor, Mention } from "@/types";
import type { DateRange } from "react-day-picker";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';

async function fetchFromAPI<T>(endpoint: string): Promise<T> {
  try {
    const response = await fetch(`${API_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`Error en la API: ${response.statusText}`);
    }
    return response.json();
  } catch (error) {
    console.error(`Falló la petición a ${endpoint}:`, error);
    throw error;
  }
}

// Helpers para fechas y filtros
const periodToRange = (period: string): string => {
  switch (period) {
    case '7d':
    case '30d':
    case '90d':
      return period;
    default:
      return '30d';
  }
}

const buildDateQuery = (periodOrRange: DateRange | string): string => {
  if (typeof periodOrRange === 'string') {
    const range = periodToRange(periodOrRange);
    return `?range=${encodeURIComponent(range)}`;
  }
  const { from, to } = periodOrRange || {};
  if (from && to) {
    const start = encodeURIComponent(from.toISOString());
    const end = encodeURIComponent(to.toISOString());
    return `?start_date=${start}&end_date=${end}`;
  }
  return `?range=30d`;
}

type FilterParams = { model?: string; source?: string; topic?: string; brand?: string };

const appendFilters = (qs: string, filters?: FilterParams): string => {
  if (!filters) return qs;
  const url = new URLSearchParams(qs.startsWith('?') ? qs.slice(1) : qs);
  if (filters.model && filters.model !== 'all') url.set('model', filters.model);
  if (filters.source && filters.source !== 'all') url.set('source', filters.source);
  if (filters.topic && filters.topic !== 'all') url.set('topic', filters.topic);
  if (filters.brand) url.set('brand', filters.brand);
  return `?${url.toString()}`;
}

export const getVisibility = (periodOrRange: DateRange | string, filters?: FilterParams): Promise<VisibilityApiResponse> => {
  const qs = appendFilters(buildDateQuery(periodOrRange), filters);
  return fetchFromAPI<VisibilityApiResponse>(`/api/visibility${qs}`);
};

export interface ShareOfVoiceResponse { overall_ranking: Competitor[]; by_topic: Record<string, Competitor[]> }
export const getShareOfVoice = (periodOrRange: DateRange | string, filters?: FilterParams): Promise<ShareOfVoiceResponse> => {
  const qs = appendFilters(buildDateQuery(periodOrRange), filters);
  return fetchFromAPI<ShareOfVoiceResponse>(`/api/industry/ranking${qs}`);
};

export const getMentions = (periodOrRange: DateRange | string, filters?: FilterParams): Promise<{ mentions: Mention[] }> => {
  const qs = appendFilters(buildDateQuery(periodOrRange), filters);
  return fetchFromAPI<{ mentions: Mention[] }>(`/api/mentions${qs}`);
};

export interface VisibilityApiResponse {
  visibility_score: number;
  delta: number;
  series: VisibilityData[];
}

export const getTopics = (): Promise<{ topics: string[] }> => fetchFromAPI<{ topics: string[] }>(`/api/topics`);
export const getModels = (): Promise<{ models: string[] }> => fetchFromAPI<{ models: string[] }>(`/api/models`);
export const getSources = (): Promise<{ sources: string[] }> => fetchFromAPI<{ sources: string[] }>(`/api/sources`);

// Sentiment
export interface SentimentApiResponse {
  timeseries: { date: string; avg: number }[];
  distribution: { negative: number; neutral: number; positive: number };
  negatives: { id: number; summary: string | null; key_topics: string[]; source_title: string | null; source_url: string | null; sentiment: number; created_at: string | null }[];
  positives?: { id: number; summary: string | null; key_topics: string[]; source_title: string | null; source_url: string | null; sentiment: number; created_at: string | null }[];
}

export const getSentiment = (periodOrRange: DateRange | string, filters?: FilterParams): Promise<SentimentApiResponse> => {
  const qs = appendFilters(buildDateQuery(periodOrRange), filters);
  return fetchFromAPI<SentimentApiResponse>(`/api/sentiment${qs}`);
};

export interface TopicsCloudResponse { topics: { topic: string; count: number; avg_sentiment: number }[] }
export const getTopicsCloud = (periodOrRange: DateRange | string, filters?: FilterParams): Promise<TopicsCloudResponse> => {
  const qs = appendFilters(buildDateQuery(periodOrRange), filters);
  return fetchFromAPI<TopicsCloudResponse>(`/api/topics-cloud${qs}`);
};

// Prompts
export interface PromptMetrics { id: number; query: string; visibility_score: number; rank: number; share_of_voice: number; executions: number }
export interface PromptsByTopic { topic: string; topic_total_mentions: number; prompts: PromptMetrics[] }
export const getPrompts = (periodOrRange: DateRange | string, filters?: FilterParams): Promise<{ topics: PromptsByTopic[] }> => {
  const qs = appendFilters(buildDateQuery(periodOrRange), filters);
  return fetchFromAPI<{ topics: PromptsByTopic[] }>(`/api/prompts${qs}`);
};

export interface PromptDetails {
  id: number;
  query: string;
  topic: string;
  timeseries: { date: string; count: number }[];
  platforms: { name: string; value: number }[];
  executions: { id: number; created_at: string | null; engine: string; source: string; response: string; sentiment: number }[];
}

export const getPromptDetails = (id: number, periodOrRange: DateRange | string, filters?: FilterParams): Promise<PromptDetails> => {
  const qs = appendFilters(buildDateQuery(periodOrRange), filters);
  return fetchFromAPI<PromptDetails>(`/api/prompts/${id}${qs}`);
};

export interface CreatePromptPayload { query: string; topic?: string; brand?: string; language?: string; enabled?: boolean }
export interface UpdatePromptPayload { query?: string; topic?: string; brand?: string; language?: string; enabled?: boolean }

export const createPrompt = async (payload: CreatePromptPayload) => {
  const res = await fetch(`${API_URL}/api/prompts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!res.ok) throw new Error(`Error creando prompt: ${res.status} ${res.statusText}`);
  return res.json();
}

export const updatePrompt = async (id: number, payload: UpdatePromptPayload) => {
  const res = await fetch(`${API_URL}/api/prompts/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!res.ok) throw new Error(`Error actualizando prompt: ${res.status} ${res.statusText}`);
  return res.json();
}

export const deletePrompt = async (id: number) => {
  const res = await fetch(`${API_URL}/api/prompts/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Error eliminando prompt: ${res.status} ${res.statusText}`);
  return res.json();
}

// Categorization helper
export const categorizePromptApi = async (query: string, topic?: string): Promise<{ category: string; confidence: number; alternatives: { category: string; score: number }[]; suggestion?: string; suggestion_is_new?: boolean; closest_existing?: string; closest_score?: number; is_close_match?: boolean }> => {
  const res = await fetch(`${API_URL}/api/categorize`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query, topic }) });
  if (!res.ok) throw new Error(`Error categorizando prompt: ${res.status} ${res.statusText}`);
  return res.json();
}

// Insights
export interface InsightPayload { opportunities?: string[]; risks?: string[]; pain_points?: string[]; trends?: string[]; quotes?: string[]; calls_to_action?: string[]; top_themes?: string[]; topic_frequency?: Record<string, number>; competitors?: string[]; brands?: string[]; avg_sentiment?: number }
export interface InsightRow { id: number; query_id: number; payload: InsightPayload; created_at: string | null }

export const getInsights = (periodOrRange: DateRange | string, filters?: FilterParams, limit: number = 50, offset: number = 0): Promise<{ insights: InsightRow[]; pagination?: { limit: number; offset: number; count: number } }> => {
  const baseQs = appendFilters(buildDateQuery(periodOrRange), filters);
  const url = new URLSearchParams(baseQs.startsWith('?') ? baseQs.slice(1) : baseQs);
  url.set('limit', String(limit));
  url.set('offset', String(offset));
  return fetchFromAPI(`/api/insights?${url.toString()}`);
};