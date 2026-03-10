import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "../../lib/auth";
import { getSavedPapers } from "../../lib/queries";

export default async function SavedPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const saved = await getSavedPapers(session.user.id);

  return (
    <main className="grid">
      <section className="saved-list">
        <p className="subtle">Saved papers</p>
        <h1>Your reading queue</h1>
        {saved.length ? (
          <div className="digest-grid">
            {saved.map((paper) => (
              <article key={paper.id} className="paper-card">
                <h2>
                  <Link href={`/papers/${paper.id}`}>{paper.title}</Link>
                </h2>
                <p className="subtle">
                  {paper.authors.join(", ")} · {new Date(paper.published_at).toLocaleDateString()}
                </p>
                <p>{paper.abstract}</p>
                <div className="chip-row">
                  {paper.categories.map((category) => (
                    <span key={category} className="meta-chip">
                      {category}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>You have not saved any papers yet.</p>
          </div>
        )}
      </section>
    </main>
  );
}
