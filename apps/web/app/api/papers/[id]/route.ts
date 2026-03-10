import { NextResponse } from "next/server";
import { auth } from "../../../../lib/auth";
import { fetchPaper } from "../../../../lib/worker";

export async function GET(
  _request: Request,
  context: {
    params: Promise<{ id: string }>;
  }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await context.params;
  const paper = await fetchPaper(session.user.id, id);
  return NextResponse.json(paper);
}
