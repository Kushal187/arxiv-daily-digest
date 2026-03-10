import { NextResponse } from "next/server";
import { auth } from "../../../lib/auth";
import { fetchDigest } from "../../../lib/worker";

export async function GET(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const date = new URL(request.url).searchParams.get("date") ?? new Date().toISOString().slice(0, 10);
  const digest = await fetchDigest(session.user.id, date);

  return NextResponse.json(digest);
}
