import { redirect } from "next/navigation";
import { OnboardingForm } from "../../components/onboarding-form";
import { auth } from "../../lib/auth";
import { getUserPreferences } from "../../lib/queries";

export default async function SettingsPage() {
  const session = await auth();

  if (!session?.user?.id) {
    redirect("/");
  }

  const preferences = await getUserPreferences(session.user.id);

  return (
    <OnboardingForm
      initialTopics={preferences.topics}
      initialAuthors={preferences.followedAuthors}
      initialCategories={preferences.categories}
      title="Settings"
      description="Adjust topics, authors, and categories that seed your ranking model."
      submitLabel="Save preferences"
    />
  );
}
