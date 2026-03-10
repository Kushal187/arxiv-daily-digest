import type { DigestResponse, PaperDetailResponse } from "@arxiv-digest/shared";
import { env } from "./env";

async function callWorker<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${env.workerBaseUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.workerInternalToken}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Worker request failed (${response.status}): ${body}`);
  }

  return (await response.json()) as T;
}

export async function fetchDigest(userId: string, date: string) {
  return callWorker<DigestResponse>(
    `/internal/recommendations/digest?userId=${encodeURIComponent(userId)}&date=${encodeURIComponent(date)}`
  );
}

export async function fetchPaper(userId: string, paperId: string) {
  return callWorker<PaperDetailResponse>(
    `/internal/papers/${encodeURIComponent(paperId)}?userId=${encodeURIComponent(userId)}`
  );
}
