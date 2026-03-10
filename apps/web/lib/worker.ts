import type { DigestResponse, PaperDetailResponse } from "@arxiv-digest/shared";
import { loadCachedUserPayload } from "./cache";
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
  const result = await loadCachedUserPayload({
    userId,
    namespace: "digest",
    identity: date,
    ttlSeconds: 60 * 15,
    load: () =>
      callWorker<DigestResponse>(
        `/internal/recommendations/digest?userId=${encodeURIComponent(userId)}&date=${encodeURIComponent(date)}`
      )
  });
  return result.value;
}

export async function fetchPaper(userId: string, paperId: string) {
  const result = await loadCachedUserPayload({
    userId,
    namespace: "paper",
    identity: paperId,
    ttlSeconds: 60 * 30,
    load: () =>
      callWorker<PaperDetailResponse>(
        `/internal/papers/${encodeURIComponent(paperId)}?userId=${encodeURIComponent(userId)}`
      )
  });
  return result.value;
}

export function fetchDigestWithCacheStatus(userId: string, date: string) {
  return loadCachedUserPayload({
    userId,
    namespace: "digest",
    identity: date,
    ttlSeconds: 60 * 15,
    load: () =>
      callWorker<DigestResponse>(
        `/internal/recommendations/digest?userId=${encodeURIComponent(userId)}&date=${encodeURIComponent(date)}`
      )
  });
}

export function fetchPaperWithCacheStatus(userId: string, paperId: string) {
  return loadCachedUserPayload({
    userId,
    namespace: "paper",
    identity: paperId,
    ttlSeconds: 60 * 30,
    load: () =>
      callWorker<PaperDetailResponse>(
        `/internal/papers/${encodeURIComponent(paperId)}?userId=${encodeURIComponent(userId)}`
      )
  });
}

export async function refreshUserProfile(userId: string) {
  try {
    await callWorker<{ ok: boolean }>(
      `/internal/users/${encodeURIComponent(userId)}/refresh-profile`,
      { method: "POST" }
    );
  } catch {
    // Profile refresh is best-effort; stale profile will be recomputed on next digest request.
  }
}
