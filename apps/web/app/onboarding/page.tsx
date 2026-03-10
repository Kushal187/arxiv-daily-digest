import { redirect } from "next/navigation";
import { OnboardingForm } from "../../components/onboarding-form";
import { auth } from "../../lib/auth";
import { getUserPreferences } from "../../lib/queries";

export default async function OnboardingPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const preferences = await getUserPreferences(session.user.id);

  if (preferences.onboardingCompleted && preferences.topics.length >= 3) {
    redirect("/digest");
  }

  return (
    <OnboardingForm
      initialTopics={preferences.topics}
      initialAuthors={preferences.followedAuthors}
      initialCategories={preferences.categories}
      title="Tune your daily research feed"
      description="Pick a focused set of topics so the first digest has a useful cold-start profile."
      submitLabel="Build my digest"
    />
  );
}
