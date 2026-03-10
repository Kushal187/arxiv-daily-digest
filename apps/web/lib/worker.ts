import type { DigestPaper } from "@arxiv-digest/shared";
import { env } from "./env";

type WorkerDigestResponse = {
  date: string;
  papers: DigestPaper[];
};

type WorkerPaperResponse = {
  paper: DigestPaper | null;
  summary: string | null;
};

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
  return callWorker<WorkerDigestResponse>(
    `/internal/recommendations/digest?userId=${encodeURIComponent(userId)}&date=${encodeURIComponent(date)}`
  );
}

export async function fetchPaper(userId: string, paperId: string) {
  return callWorker<WorkerPaperResponse>(
    `/internal/papers/${encodeURIComponent(paperId)}?userId=${encodeURIComponent(userId)}`
  );
}
