import { NextResponse } from "next/server";
import type { PreferencesPayload } from "@arxiv-digest/shared";
import { auth } from "../../../lib/auth";
import { replacePreferences } from "../../../lib/queries";

export async function PUT(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = (await request.json()) as PreferencesPayload;
  if (!Array.isArray(payload.topics) || payload.topics.length < 3 || payload.topics.length > 8) {
    return NextResponse.json({ error: "Select between 3 and 8 topics" }, { status: 400 });
  }

  await replacePreferences(session.user.id, {
    topics: payload.topics,
    followedAuthors: Array.isArray(payload.followedAuthors) ? payload.followedAuthors : [],
    categories: Array.isArray(payload.categories) ? payload.categories : []
  });

  return NextResponse.json({ ok: true });
}
