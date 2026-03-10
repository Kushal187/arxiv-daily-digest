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
    <main className="grid">
      <section className="panel">
        <p className="subtle">Today&apos;s ranked feed</p>
        <h1>{digest.date}</h1>
        <p>
          Ranked against your selected topics, category preferences, followed authors, saved papers,
          and dismissal history.
        </p>
      </section>

      <section className="digest-grid">
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
