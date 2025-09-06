// frontend/types.ts

export interface Mention {
    id: number;
    engine?: string | null;
    source?: string | null;
    response?: string | null;
    sentiment?: number | null;
    emotion?: string | null;
    confidence_score?: number | null;
    source_title?: string | null;
    source_url?: string | null;
    language?: string | null;
    created_at?: string | null; // ISO string
    query?: string | null;
    summary?: string | null;
    key_topics?: string[] | null;
    generated_insight_id?: number | null;
}
  
  export interface VisibilityData {
      date: string;
      value: number;
  }
  
  export interface Competitor {
      rank: number;
      name: string;
      score: string;
      change: string;
      positive: boolean;
      color: string;
      selected?: boolean;
  }
  
  // ...y cualquier otra estructura de datos que tu API vaya a enviar.