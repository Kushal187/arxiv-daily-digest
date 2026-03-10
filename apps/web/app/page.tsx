import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "../lib/auth";
import { getUserPreferences } from "../lib/queries";

export default async function HomePage() {
  const session = await auth();

  if (session?.user?.id) {
    const preferences = await getUserPreferences(session.user.id);
    redirect(preferences.onboardingCompleted && preferences.topics.length >= 3 ? "/digest" : "/onboarding");
  }

  return (
    <main className="page">
      <section className="intro-page">
        <p className="eyebrow">tool, not product</p>
        <h1>See what matters today, not just what was uploaded.</h1>
        <p>
          The digest ingests fresh arXiv papers, tags them with a curated ML taxonomy, clusters
          themes, and ranks papers using your interests and interactions.
        </p>
        <p className="reason-line">daily ranked feed · interpretable match reasons · save and dismiss feedback loop</p>
        <div className="paper-actions compact landing-actions">
          <a className="action-link prominent" href="/api/auth/signin">
            Sign in with Google
          </a>
          <Link className="action-link prominent" href="/digest">
            Preview routes
          </Link>
        </div>
      </section>
    </main>
  );
}
