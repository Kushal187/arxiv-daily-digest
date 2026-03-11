import Link from "next/link";
import { redirect } from "next/navigation";
import { getAreaLabel } from "@arxiv-digest/shared";
import { DiscoverGrid } from "../../components/discover-grid";
import { auth } from "../../lib/auth";
import { formatCalendarDate, isCalendarDateString, utcCalendarDateString } from "../../lib/dates";
import { getUserPreferences } from "../../lib/queries";
import { fetchDiscover } from "../../lib/worker";

export default async function DiscoverPage({
  searchParams
}: {
  searchParams: Promise<{ date?: string | string[]; area?: string | string[] }>;
}) {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const params = await searchParams;
  const requestedDate = Array.isArray(params.date) ? params.date[0] : params.date;
  const requestedArea = Array.isArray(params.area) ? params.area[0] : params.area;

  if (!requestedDate || !isCalendarDateString(requestedDate)) {
    redirect(`/discover?date=${utcCalendarDateString()}`);
  }

  const preferences = await getUserPreferences(session.user.id);
  if (!preferences.onboardingCompleted || preferences.areas.length < 3) {
    redirect("/onboarding");
  }

  const activeArea = preferences.areas.find((area) => area === requestedArea);
  const discover = await fetchDiscover(session.user.id, requestedDate, activeArea);

  return (
    <main className="page">
      <section className="page-header">
        <p className="eyebrow">discover</p>
        <h1>What you may have missed</h1>
        <p className="page-description">
          Curated over the last {discover.windowDays} days for fast scanning across your selected research areas.
        </p>
        <p className="section-note">Window ending {formatCalendarDate(discover.resolvedDate)}.</p>
      </section>

      <section className="feed-toolbar">
        <div className="filter-pills" role="tablist" aria-label="Discover area filters">
          <Link
            className={activeArea ? "filter-pill link-pill" : "filter-pill active link-pill"}
            href={`/discover?date=${requestedDate}`}
          >
            All selected areas
          </Link>
          {preferences.areas.map((area) => (
            <Link
              key={area}
              className={activeArea === area ? "filter-pill active link-pill" : "filter-pill link-pill"}
              href={`/discover?date=${requestedDate}&area=${area}`}
            >
              {getAreaLabel(area)}
            </Link>
          ))}
        </div>
      </section>

      {discover.papers.length ? (
        <DiscoverGrid discover={discover} />
      ) : (
        <section className="feed-list">
          <div className="empty-state">
            <p>No papers matched this discover view yet. Try a different area or widen your categories.</p>
          </div>
        </section>
      )}
    </main>
  );
}
