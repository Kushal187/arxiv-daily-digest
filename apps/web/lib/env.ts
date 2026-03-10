const required = [
  "DATABASE_URL",
  "NEXTAUTH_SECRET",
  "GOOGLE_CLIENT_ID",
  "GOOGLE_CLIENT_SECRET",
  "WORKER_BASE_URL",
  "WORKER_INTERNAL_TOKEN"
] as const;

type RequiredKey = (typeof required)[number];

function readEnv(key: RequiredKey): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }

  return value;
}

export const env = {
  databaseUrl: readEnv("DATABASE_URL"),
  nextAuthSecret: readEnv("NEXTAUTH_SECRET"),
  googleClientId: readEnv("GOOGLE_CLIENT_ID"),
  googleClientSecret: readEnv("GOOGLE_CLIENT_SECRET"),
  workerBaseUrl: readEnv("WORKER_BASE_URL"),
  workerInternalToken: readEnv("WORKER_INTERNAL_TOKEN"),
  explainEnabled: process.env.ENABLE_PAPER_EXPLAIN === "true"
};
