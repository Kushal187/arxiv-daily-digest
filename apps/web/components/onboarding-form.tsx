"use client";

import { useState } from "react";
import {
  DEFAULT_ARXIV_CATEGORIES,
  TOPIC_TAXONOMY,
  type PreferencesPayload,
  type TopicSlug
} from "@arxiv-digest/shared";

type Props = {
  initialTopics: string[];
  initialAuthors: string[];
  initialCategories: string[];
  title: string;
  description: string;
  submitLabel: string;
};

export function OnboardingForm({
  initialTopics,
  initialAuthors,
  initialCategories,
  title,
  description,
  submitLabel
}: Props) {
  const [topics, setTopics] = useState<TopicSlug[]>(initialTopics as TopicSlug[]);
  const [authors, setAuthors] = useState(initialAuthors.join(", "));
  const [categories, setCategories] = useState<string[]>(
    initialCategories.length ? initialCategories : [...DEFAULT_ARXIV_CATEGORIES]
  );
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  function toggleTopic(slug: TopicSlug) {
    setTopics((current) =>
      current.includes(slug) ? current.filter((item) => item !== slug) : [...current, slug]
    );
  }

  function toggleCategory(value: string) {
    setCategories((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value]
    );
  }

  async function onSubmit() {
    if (topics.length < 3 || topics.length > 8) {
      setError("Choose between 3 and 8 topics.");
      return;
    }

    const payload: PreferencesPayload = {
      topics,
      followedAuthors: authors
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean),
      categories
    };

    try {
      setIsPending(true);
      setError(null);
      const response = await fetch("/api/preferences", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        setError("Could not save your preferences.");
        return;
      }

      window.location.href = "/digest";
    } finally {
      setIsPending(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h1>{title}</h1>
        <p className="subtle">{description}</p>
      </div>

      <div className="section-block">
        <h2>Pick your topics</h2>
        <p className="subtle">Choose 3 to 8. These seed your cold-start ranking profile.</p>
        <div className="topic-grid">
          {TOPIC_TAXONOMY.map((topic) => (
            <button
              key={topic.slug}
              type="button"
              className={topics.includes(topic.slug) ? "taxonomy-chip active" : "taxonomy-chip"}
              onClick={() => toggleTopic(topic.slug)}
            >
              <strong>{topic.label}</strong>
              <span>{topic.description}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="section-block">
        <h2>Follow authors</h2>
        <p className="subtle">Optional comma-separated list of labs or researchers you track.</p>
        <textarea
          className="text-input"
          rows={3}
          value={authors}
          onChange={(event) => setAuthors(event.target.value)}
          placeholder="Yann LeCun, Chelsea Finn, Percy Liang"
        />
      </div>

      <div className="section-block">
        <h2>Preferred arXiv categories</h2>
        <div className="chip-row">
          {DEFAULT_ARXIV_CATEGORIES.map((category) => (
            <button
              key={category}
              type="button"
              className={categories.includes(category) ? "meta-chip active" : "meta-chip"}
              onClick={() => toggleCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <button className="primary-button" disabled={isPending} onClick={onSubmit}>
        {isPending ? "Saving..." : submitLabel}
      </button>
    </section>
  );
}
