import type { PreferencesPayload } from "@arxiv-digest/shared";
import { matchFollowedAuthors } from "./authors";
import { sql } from "./db";

export type AppUserRecord = {
  id: string;
  email: string;
  onboardingCompleted: boolean;
  preferredCategories: string[];
};

type EnsureUserInput = {
  email: string;
  name: string | null;
  image: string | null;
  providerSubject: string | null;
};

export async function ensureUserRecord(input: EnsureUserInput): Promise<AppUserRecord> {
  const rows = await sql<{
    id: string;
    email: string;
    onboarding_completed: boolean;
    preferred_categories: string[];
  }[]>`
    insert into users (email, name, image, provider_subject)
    values (${input.email}, ${input.name}, ${input.image}, ${input.providerSubject})
    on conflict (email)
    do update
      set name = excluded.name,
          image = excluded.image,
          provider_subject = coalesce(excluded.provider_subject, users.provider_subject),
          updated_at = now()
    returning id, email, onboarding_completed, preferred_categories
  `;

  const row = rows[0];

  return {
    id: row.id,
    email: row.email,
    onboardingCompleted: row.onboarding_completed,
    preferredCategories: row.preferred_categories ?? []
  };
}

export async function getUserByEmail(email: string): Promise<AppUserRecord | null> {
  const rows = await sql<{
    id: string;
    email: string;
    onboarding_completed: boolean;
    preferred_categories: string[];
  }[]>`
    select id, email, onboarding_completed, preferred_categories
    from users
    where email = ${email}
    limit 1
  `;

  const row = rows[0];
  if (!row) {
    return null;
  }

  return {
    id: row.id,
    email: row.email,
    onboardingCompleted: row.onboarding_completed,
    preferredCategories: row.preferred_categories ?? []
  };
}

export async function getUserById(id: string): Promise<AppUserRecord | null> {
  const rows = await sql<{
    id: string;
    email: string;
    onboarding_completed: boolean;
    preferred_categories: string[];
  }[]>`
    select id, email, onboarding_completed, preferred_categories
    from users
    where id = ${id}
    limit 1
  `;

  const row = rows[0];
  if (!row) {
    return null;
  }

  return {
    id: row.id,
    email: row.email,
    onboardingCompleted: row.onboarding_completed,
    preferredCategories: row.preferred_categories ?? []
  };
}

export async function getUserPreferences(userId: string) {
  const [topicRows, authorRows, userRows] = await Promise.all([
    sql<{ topic_slug: string }[]>`
      select topic_slug
      from user_topic_preferences
      where user_id = ${userId}
      order by topic_slug asc
    `,
    sql<{ author_name: string }[]>`
      select author_name
      from user_followed_authors
      where user_id = ${userId}
      order by author_name asc
    `,
    sql<{ preferred_categories: string[]; onboarding_completed: boolean }[]>`
      select preferred_categories, onboarding_completed
      from users
      where id = ${userId}
      limit 1
    `
  ]);

  return {
    topics: topicRows.map((row) => row.topic_slug),
    followedAuthors: authorRows.map((row) => row.author_name),
    categories: userRows[0]?.preferred_categories ?? [],
    onboardingCompleted: Boolean(userRows[0]?.onboarding_completed)
  };
}

export async function replacePreferences(userId: string, payload: PreferencesPayload) {
  await sql.begin(async (tx) => {
    await tx`
      update users
      set preferred_categories = ${payload.categories},
          onboarding_completed = true,
          updated_at = now()
      where id = ${userId}
    `;

    await tx`delete from user_topic_preferences where user_id = ${userId}`;
    await tx`delete from user_followed_authors where user_id = ${userId}`;

    for (const topic of payload.topics) {
      await tx`
        insert into user_topic_preferences (user_id, topic_slug, weight)
        values (${userId}, ${topic}, 1)
      `;
    }

    for (const author of payload.followedAuthors) {
      await tx`
        insert into user_followed_authors (user_id, author_name)
        values (${userId}, ${author})
      `;
    }
  });
}

export async function recordInteraction(userId: string, paperId: string, action: string) {
  if (action === "unsave") {
    await sql`
      delete from user_interactions
      where user_id = ${userId}
        and paper_id = ${paperId}
        and interaction_type = 'save'
    `;

    return;
  }

  await sql`
    insert into user_interactions (user_id, paper_id, interaction_type)
    values (${userId}, ${paperId}, ${action})
    on conflict (user_id, paper_id, interaction_type) do nothing
  `;
}

export async function getSavedPapers(userId: string) {
  const rows = await sql<{
    id: string;
    source_id: string;
    title: string;
    abstract: string;
    authors: string[];
    categories: string[];
    primary_category: string;
    published_at: string;
    updated_at: string;
    url: string;
  }[]>`
    select
      p.id,
      p.source_id,
      p.title,
      p.abstract,
      p.authors,
      p.categories,
      p.primary_category,
      p.published_at::text,
      p.updated_at::text,
      p.url
    from user_interactions ui
    join papers p on p.id = ui.paper_id
    where ui.user_id = ${userId}
      and ui.interaction_type = 'save'
    order by ui.created_at desc
  `;

  return rows;
}

export async function getFollowedAuthorsDashboard(userId: string) {
  const preferences = await getUserPreferences(userId);
  const followedAuthors = preferences.followedAuthors;

  const recentRows = await sql<{
    id: string;
    title: string;
    authors: string[];
    published_at: string;
    url: string;
  }[]>`
    select id, title, authors, published_at::text, url
    from papers
    where published_at >= now() - interval '90 days'
    order by published_at desc
    limit 300
  `;

  const perAuthor = new Map(
    followedAuthors.map((author) => [
      author,
      {
        name: author,
        recentMatchCount: 0,
        recentMatches: [] as {
          id: string;
          title: string;
          authors: string[];
          publishedAt: string;
          url: string;
          matchedPaperAuthor: string;
        }[]
      }
    ])
  );

  for (const paper of recentRows) {
    const matches = matchFollowedAuthors(followedAuthors, paper.authors);
    for (const match of matches) {
      const bucket = perAuthor.get(match.followed);
      if (!bucket) {
        continue;
      }

      bucket.recentMatchCount += 1;
      if (bucket.recentMatches.length < 5) {
        bucket.recentMatches.push({
          id: paper.id,
          title: paper.title,
          authors: paper.authors,
          publishedAt: paper.published_at,
          url: paper.url,
          matchedPaperAuthor: match.paperAuthor
        });
      }
    }
  }

  const authors = Array.from(perAuthor.values()).sort(
    (left, right) => right.recentMatchCount - left.recentMatchCount || left.name.localeCompare(right.name)
  );

  const recentPapers = authors
    .flatMap((author) =>
      author.recentMatches.map((paper) => ({
        ...paper,
        followedAuthor: author.name
      }))
    )
    .sort((left, right) => right.publishedAt.localeCompare(left.publishedAt))
    .slice(0, 15);

  return { authors, recentPapers };
}
