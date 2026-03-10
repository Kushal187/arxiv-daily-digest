import { NextResponse } from "next/server";
import { auth } from "../../../lib/auth";
import { invalidateUserCache } from "../../../lib/cache";
import { recordInteraction } from "../../../lib/queries";
import { refreshUserProfile } from "../../../lib/worker";

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = (await request.json()) as { paperId?: string; action?: string };
  if (!payload.paperId || !payload.action) {
    return NextResponse.json({ error: "Missing paperId or action" }, { status: 400 });
  }

  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!UUID_RE.test(payload.paperId)) {
    return NextResponse.json({ error: "Invalid paperId format" }, { status: 400 });
  }

  if (!["open", "save", "dismiss", "unsave", "undismiss"].includes(payload.action)) {
    return NextResponse.json({ error: "Unsupported action" }, { status: 400 });
  }

  await recordInteraction(session.user.id, payload.paperId, payload.action);
  if (payload.action !== "open") {
    await invalidateUserCache(session.user.id);
    refreshUserProfile(session.user.id);
  }

  return NextResponse.json({ ok: true });
}
