import { NextResponse } from "next/server";
import { normalizeAreaSlugs, type PreferencesPayload } from "@arxiv-digest/shared";
import { auth } from "../../../lib/auth";
import { invalidateUserCache, PREFERENCE_AND_RANKING_NAMESPACES } from "../../../lib/cache";
import { replacePreferences } from "../../../lib/queries";
import { refreshUserProfile } from "../../../lib/worker";

export async function PUT(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = (await request.json()) as PreferencesPayload;
  const areas = normalizeAreaSlugs(payload.areas ?? payload.topics ?? []);
  if (areas.length < 3 || areas.length > 8) {
    return NextResponse.json({ error: "Select between 3 and 8 research areas" }, { status: 400 });
  }

  await replacePreferences(session.user.id, {
    areas,
    followedAuthors: Array.isArray(payload.followedAuthors) ? payload.followedAuthors : [],
    categories: Array.isArray(payload.categories) ? payload.categories : []
  });
  await invalidateUserCache(session.user.id, PREFERENCE_AND_RANKING_NAMESPACES);
  refreshUserProfile(session.user.id);

  return NextResponse.json({ ok: true });
}
