import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "../lib/auth";
import { getUserPreferences } from "../lib/queries";
import { SignInButton } from "../components/sign-in-button";

export default async function HomePage() {
  const session = await auth();

  if (session?.user?.id) {
    const preferences = await getUserPreferences(session.user.id);
    redirect(preferences.onboardingCompleted && preferences.topics.length >= 3 ? "/digest" : "/onboarding");
  }

  return (
    <main className="landing">
      <section className="hero">
        <p className="hero-eyebrow">tool, not product</p>
        <h1 className="hero-title">
          See what matters today,
          <br />
          not just what was uploaded.
        </h1>
        <p className="hero-subtitle">
          A daily digest that ingests fresh arXiv papers, tags them with a curated ML taxonomy,
          clusters themes, and ranks papers using your interests and interactions.
        </p>
        <div className="hero-cta">
          <SignInButton className="cta-primary" />
          <Link className="cta-secondary" href="/digest">
            Browse without signing in
          </Link>
        </div>
      </section>

      <hr className="landing-divider" />

      <section className="features">
        <div className="feature">
          <span className="feature-icon">&#9670;</span>
          <h3 className="feature-heading">Ranked daily feed</h3>
          <p className="feature-text">
            Papers scored and ordered by relevance to your research interests, not just recency.
          </p>
        </div>
        <div className="feature">
          <span className="feature-icon">&#9674;</span>
          <h3 className="feature-heading">Interpretable match reasons</h3>
          <p className="feature-text">
            See exactly why each paper surfaced — topic overlap, author connections, citation patterns.
          </p>
        </div>
        <div className="feature">
          <span className="feature-icon">&#9675;</span>
          <h3 className="feature-heading">Save &amp; dismiss feedback</h3>
          <p className="feature-text">
            Bookmark what&apos;s useful, dismiss what&apos;s not. The ranking improves with every action.
          </p>
        </div>
      </section>

      <footer className="landing-footer">
        <p>Built for ML researchers who read arXiv daily.</p>
      </footer>
    </main>
  );
}
