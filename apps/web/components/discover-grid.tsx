import type { DiscoverResponse } from "@arxiv-digest/shared";
import { DiscoverCard } from "./discover-card";

export function DiscoverGrid({ discover }: { discover: DiscoverResponse }) {
  return (
    <section className="discover-grid">
      {discover.papers.map((paper) => (
        <DiscoverCard key={paper.id} paper={paper} />
      ))}
    </section>
  );
}
