import { Redis } from "@upstash/redis";

export type CacheNamespace = "digest" | "paper" | "preferences";
export type CacheStatus = "hit" | "miss" | "bypass" | "error";

type CachedLoadOptions<T> = {
  userId: string;
  namespace: CacheNamespace;
  identity: string;
  ttlSeconds: number;
  load: () => Promise<T>;
};

const CACHE_PREFIX = "arxiv-digest";
const RANKING_NAMESPACES: CacheNamespace[] = ["digest", "paper"];
export const PREFERENCE_AND_RANKING_NAMESPACES: CacheNamespace[] = ["preferences", ...RANKING_NAMESPACES];

let redisClient: Redis | null | undefined;

function getRedisClient() {
  if (redisClient !== undefined) {
    return redisClient;
  }

  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;

  redisClient = url && token ? new Redis({ url, token }) : null;
  return redisClient;
}

export function resetCacheClientForTests() {
  redisClient = undefined;
}

function payloadKey(namespace: CacheNamespace, userId: string, identity: string) {
  return `${CACHE_PREFIX}:${namespace}:user:${userId}:payload:${identity}`;
}

function invalidatedAtKey(namespace: CacheNamespace, userId: string) {
  return `${CACHE_PREFIX}:${namespace}:user:${userId}:invalidated-at`;
}

export async function loadCachedUserPayload<T>({
  userId,
  namespace,
  identity,
  ttlSeconds,
  load
}: CachedLoadOptions<T>): Promise<{ value: T; status: CacheStatus }> {
  const redis = getRedisClient();
  if (!redis) {
    return { value: await load(), status: "bypass" };
  }

  try {
    const [invalidatedAt, cached] = await redis
      .pipeline()
      .get<number | string>(invalidatedAtKey(namespace, userId))
      .get<{ createdAt: number; value: T }>(payloadKey(namespace, userId, identity))
      .exec();

    const invalidatedAtValue = Number(invalidatedAt ?? 0);
    if (cached && cached.createdAt > invalidatedAtValue) {
      return { value: cached.value, status: "hit" };
    }

    const payload = await load();
    try {
      await redis.set(
        payloadKey(namespace, userId, identity),
        { createdAt: Date.now(), value: payload },
        { ex: ttlSeconds }
      );
    } catch {
      // A cache write failure should not force a second worker fetch.
    }
    return { value: payload, status: "miss" };
  } catch {
    return { value: await load(), status: "error" };
  }
}

export async function invalidateUserCache(userId: string, namespaces: CacheNamespace[] = RANKING_NAMESPACES) {
  const redis = getRedisClient();
  if (!redis) {
    return;
  }

  try {
    const timestamp = Date.now();
    const pipeline = redis.pipeline();

    for (const namespace of namespaces) {
      pipeline.set(invalidatedAtKey(namespace, userId), timestamp);
    }

    await pipeline.exec();
  } catch {
    // Cache invalidation should never block the primary write path.
  }
}

