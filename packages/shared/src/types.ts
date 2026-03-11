import type { ResearchAreaSlug } from "./topics";

export type InteractionType = "open" | "save" | "dismiss" | "unsave" | "undismiss";

export type RecommendationReason =
  | { type: "topic"; label: string; score: number }
  | { type: "saved_similarity"; label: string; score: number }
  | { type: "author"; label: string; score: number }
  | { type: "category"; label: string; score: number }
  | { type: "freshness"; label: string; score: number }
  | { type: "cluster"; label: string; score: number };

export type PaperTopic = {
  slug: string;
  areaSlug: ResearchAreaSlug | null;
  confidence: number;
  isHidden: boolean;
};

export type DigestPaper = {
  id: string;
  sourceId: string;
  canonicalArxivId: string;
  arxivVersion: number;
  title: string;
  abstract: string;
  authors: string[];
  categories: string[];
  primaryCategory: string;
  publishedAt: string;
  updatedAt: string;
  url: string;
  clusterLabel: string;
  topics: PaperTopic[];
  reasons: RecommendationReason[];
  score: number;
  isSaved: boolean;
  isDismissed: boolean;
};

export type DigestResponse = {
  requestedDate: string;
  resolvedDate: string;
  isFallback: boolean;
  didBackfillCategories: boolean;
  papers: DigestPaper[];
};

export type DiscoverResponse = {
  requestedDate: string;
  resolvedDate: string;
  windowDays: number;
  selectedArea: ResearchAreaSlug | null;
  papers: DigestPaper[];
};

export type SummarySource = "extractive" | "llm";

export type PaperDetailResponse = {
  paper: DigestPaper | null;
  summary: string | null;
  summarySource: SummarySource | null;
};

export type PreferencesPayload = {
  areas?: ResearchAreaSlug[];
  topics?: string[];
  followedAuthors: string[];
  categories: string[];
};
