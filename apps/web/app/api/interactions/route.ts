import { NextResponse } from "next/server";
import { auth } from "../../../lib/auth";
import { recordInteraction } from "../../../lib/queries";

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = (await request.json()) as { paperId?: string; action?: string };
  if (!payload.paperId || !payload.action) {
    return NextResponse.json({ error: "Missing paperId or action" }, { status: 400 });
  }

  if (!["open", "save", "dismiss", "unsave"].includes(payload.action)) {
    return NextResponse.json({ error: "Unsupported action" }, { status: 400 });
  }

  await recordInteraction(session.user.id, payload.paperId, payload.action);

  return NextResponse.json({ ok: true });
}
