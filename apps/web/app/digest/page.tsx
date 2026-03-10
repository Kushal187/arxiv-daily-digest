import { redirect } from "next/navigation";
import { DigestCard } from "../../components/digest-card";
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
      <section className="page-header">
        <p className="eyebrow">daily digest</p>
        <h1>{new Date(digest.date).toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" })}</h1>
        <p className="page-description">
          Ranked against selected topics, followed authors, category preferences, saved papers, and
          dismissals.
        </p>
      </section>

      <section className="feed-list">
        {digest.papers.length ? (
          digest.papers.map((paper) => <DigestCard key={paper.id} paper={paper} />)
        ) : (
          <div className="empty-state">
            <p>No papers are available for this day yet. Run the ingest job or widen the category set.</p>
          </div>
        )}
      </section>
    </main>
  );
}
