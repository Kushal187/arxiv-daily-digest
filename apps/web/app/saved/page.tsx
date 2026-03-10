import { redirect } from "next/navigation";
import { SavedQueue } from "../../components/saved-queue";
import { auth } from "../../lib/auth";
import { getSavedPapers } from "../../lib/queries";

export default async function SavedPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const saved = await getSavedPapers(session.user.id);

  return (
    <main className="page">
      <section className="page-header">
        <p className="eyebrow">saved</p>
        <h1>Your reading queue</h1>
        <p className="page-description">Sort by when you saved papers or when they were published.</p>
      </section>
      {saved.length ? (
        <SavedQueue papers={saved} />
      ) : (
        <section className="feed-list">
          <div className="empty-state">
            <p>You have not saved any papers yet.</p>
          </div>
        </section>
      )}
    </main>
  );
}
