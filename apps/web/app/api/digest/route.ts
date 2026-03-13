import { NextResponse } from "next/server";
import { auth } from "../../../lib/auth";
import { isCalendarDateString } from "../../../lib/dates";
import { fetchDigestWithCacheStatus } from "../../../lib/worker";

export async function GET(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const date = new URL(request.url).searchParams.get("date");
  if (!date) {
    return NextResponse.json({ error: "Missing digest date" }, { status: 400 });
  }

  if (!isCalendarDateString(date)) {
    return NextResponse.json({ error: "Invalid date format. Expected YYYY-MM-DD." }, { status: 400 });
  }

  const digest = await fetchDigestWithCacheStatus(session.user.id, date);

  return NextResponse.json(digest.value, {
    headers: {
      "X-Cache": digest.status
    }
  });
}
