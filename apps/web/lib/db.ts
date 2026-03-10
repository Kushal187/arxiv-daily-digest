import postgres from "postgres";
import { env } from "./env";

declare global {
  var __arxivDigestSql: ReturnType<typeof postgres> | undefined;
}

export const sql =
  global.__arxivDigestSql ??
  postgres(env.databaseUrl, {
    prepare: false,
    max: 5,
    idle_timeout: 5
  });

if (process.env.NODE_ENV !== "production") {
  global.__arxivDigestSql = sql;
}
