"use client";

import { useState } from "react";

export function ExpandableAbstract({ abstract }: { abstract: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="expandable-abstract">
      <button
        type="button"
        className="inline-toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
      >
        {expanded ? "hide full abstract" : "show full abstract"}
      </button>
      {expanded ? <p className="paper-abstract expanded">{abstract}</p> : null}
    </div>
  );
}
