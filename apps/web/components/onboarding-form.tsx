"use client";

import { KeyboardEvent, useState } from "react";
import {
  DEFAULT_ARXIV_CATEGORIES,
  TOPIC_TAXONOMY,
  type PreferencesPayload,
  type TopicSlug
} from "@arxiv-digest/shared";
import {
  dedupeFollowedAuthors,
  normalizeFollowedAuthorDisplay,
  normalizeFollowedAuthorKey
} from "../lib/followed-authors";

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
  const [authors, setAuthors] = useState<string[]>(() => dedupeFollowedAuthors(initialAuthors));
  const [authorInput, setAuthorInput] = useState("");
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

  function addAuthor(rawValue: string) {
    const value = normalizeFollowedAuthorDisplay(rawValue);
    const key = normalizeFollowedAuthorKey(value);
    if (!value || !key) {
      return;
    }

    setAuthors((current) => {
      if (current.some((author) => normalizeFollowedAuthorKey(author) === key)) {
        return current;
      }

      return [...current, value];
    });
    setAuthorInput("");
  }

  function removeAuthor(value: string) {
    setAuthors((current) => current.filter((author) => author !== value));
  }

  function handleAuthorKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key !== "Enter" && event.key !== ",") {
      return;
    }

    event.preventDefault();
    addAuthor(authorInput);
  }

  async function onSubmit() {
    if (topics.length < 3 || topics.length > 8) {
      setError("Choose between 3 and 8 topics.");
      return;
    }

    const payload: PreferencesPayload = {
      topics,
      followedAuthors: authors,
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
    <section className="settings-page">
      <div className="page-header">
        <p className="eyebrow">preferences</p>
        <h1>{title}</h1>
        <p className="page-description">{description}</p>
      </div>

      <div className="settings-section">
        <h2>Pick your topics</h2>
        <p className="section-note">Choose 3 to 8. These seed your cold-start ranking profile.</p>
        <p className="selection-count">
          selected {topics.length} / 8
        </p>
        <div className="settings-grid">
          {TOPIC_TAXONOMY.map((topic) => (
            <label key={topic.slug} className="checkbox-row">
              <input
                type="checkbox"
                checked={topics.includes(topic.slug)}
                onChange={() => toggleTopic(topic.slug)}
              />
              <span>
                <strong>{topic.label}</strong>
                <small>{topic.description}</small>
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="settings-section">
        <h2>Follow authors</h2>
        <p className="section-note">Add researchers or labs one at a time. Press Enter or comma to add them.</p>
        <div className="author-input-wrap">
          <input
            className="text-input"
            type="text"
            value={authorInput}
            onChange={(event) => setAuthorInput(event.target.value)}
            onKeyDown={handleAuthorKeyDown}
            placeholder="Yann LeCun"
          />
          <button
            type="button"
            className="action-link prominent"
            onClick={() => addAuthor(authorInput)}
            disabled={!normalizeFollowedAuthorDisplay(authorInput)}
          >
            add author
          </button>
        </div>
        {authors.length ? (
          <div className="author-chip-list">
            {authors.map((author) => (
              <span key={author} className="author-chip">
                {author}
                <button
                  type="button"
                  className="author-chip-remove"
                  aria-label={`Remove ${author}`}
                  onClick={() => removeAuthor(author)}
                >
                  remove
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="section-note">No authors followed yet.</p>
        )}
      </div>

      <div className="settings-section">
        <div className="section-heading">
          <h2>Preferred arXiv categories</h2>
          <span className="tooltip-wrap">
            <button
              type="button"
              className="info-trigger"
              aria-label="Explain arXiv categories"
              aria-describedby="arxiv-category-tooltip"
            >
              i
            </button>
            <span id="arxiv-category-tooltip" role="tooltip" className="tooltip-bubble">
              arXiv categories are the subject buckets from arXiv itself, such as cs.AI, cs.LG,
              and cs.CL. They narrow the candidate pool first, with automatic backfill if the
              category slice is too small for a useful digest.
            </span>
          </span>
        </div>
        <div className="settings-grid compact">
          {DEFAULT_ARXIV_CATEGORIES.map((category) => (
            <label key={category} className="checkbox-row compact">
              <input
                type="checkbox"
                checked={categories.includes(category)}
                onChange={() => toggleCategory(category)}
              />
              <span>
                <strong>{category}</strong>
              </span>
            </label>
          ))}
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="form-footer">
        <button className="primary-button" disabled={isPending} onClick={onSubmit}>
          {isPending ? "saving..." : submitLabel.toLowerCase()}
        </button>
      </div>
    </section>
  );
}
