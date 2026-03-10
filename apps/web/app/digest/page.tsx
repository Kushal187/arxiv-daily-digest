import { redirect } from "next/navigation";
import { DigestFeed } from "../../components/digest-feed";
import { DigestHeader } from "../../components/digest-header";
import { auth } from "../../lib/auth";
import { getUserPreferences } from "../../lib/queries";
import { fetchDigest } from "../../lib/worker";

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

export default async function DigestPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const preferences = await getUserPreferences(session.user.id);
  if (!preferences.onboardingCompleted || preferences.topics.length < 3) {
    redirect("/onboarding");
  }

  const digest = await fetchDigest(session.user.id, todayString());

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
