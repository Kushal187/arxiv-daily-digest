import { redirect } from "next/navigation";
import { DigestFeed } from "../../components/digest-feed";
import { DigestHeader } from "../../components/digest-header";
import { auth } from "../../lib/auth";
import { isCalendarDateString, utcCalendarDateString } from "../../lib/dates";
import { getUserPreferences } from "../../lib/queries";
import { fetchDigest } from "../../lib/worker";

export default async function DigestPage({
  searchParams
}: {
  searchParams: Promise<{ date?: string | string[] }>;
}) {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const params = await searchParams;
  const requestedDate = Array.isArray(params.date) ? params.date[0] : params.date;

  if (!requestedDate || !isCalendarDateString(requestedDate)) {
    redirect(`/digest?date=${utcCalendarDateString()}`);
  }

  const [preferences, digest] = await Promise.all([
    getUserPreferences(session.user.id),
    fetchDigest(session.user.id, requestedDate)
  ]);

  if (!preferences.onboardingCompleted || preferences.topics.length < 3) {
    redirect("/onboarding");
  }

  return (
    <main className="page">
      <DigestHeader
        requestedDate={digest.requestedDate}
        resolvedDate={digest.resolvedDate}
        isFallback={digest.isFallback}
      />

      {digest.papers.length ? (
        <DigestFeed digest={digest} />
      ) : (
        <section className="feed-list">
          <div className="empty-state">
            <p>No papers are available for this day yet. Run the ingest job or widen the category set.</p>
          </div>
        </section>
      )}
    </main>
  );
}
