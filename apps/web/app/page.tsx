import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "../lib/auth";

export default async function HomePage() {
  const session = await auth();

  if (session?.user?.id) {
    redirect(session.user.onboardingCompleted ? "/digest" : "/onboarding");
  }

  return (
    <main className="grid">
      <section className="hero">
        <p className="subtle">Personalized arXiv ranking for ML researchers</p>
        <h1>See what matters today, not just what was uploaded.</h1>
        <p>
          The digest ingests fresh arXiv papers, tags them with a curated ML taxonomy, clusters
          themes, and ranks papers using your interests and interactions.
        </p>
        <div className="chip-row">
          <span className="reason-chip">Daily ranked feed</span>
          <span className="reason-chip">Interpretable match reasons</span>
          <span className="reason-chip">Save and dismiss feedback loop</span>
        </div>
        <div className="paper-actions compact">
          <a className="primary-button" href="/api/auth/signin">
            Sign in with Google
          </a>
          <Link className="primary-button" href="/digest">
            Preview routes
          </Link>
        </div>
      </section>
    </main>
  );
}
