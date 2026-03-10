import type { NextAuthConfig } from "next-auth";
import { ensureUserRecord } from "./queries";

export const authCallbacks = {
  async jwt({ token, account, profile }) {
    const enrichedToken = token as typeof token & {
      appUserId?: string;
      onboardingCompleted?: boolean;
    };

    if (account && token.email) {
      const user = await ensureUserRecord({
        email: token.email,
        name: typeof token.name === "string" ? token.name : null,
        image: typeof token.picture === "string" ? token.picture : null,
        providerSubject:
          typeof profile?.sub === "string"
            ? profile.sub
            : typeof account.providerAccountId === "string"
              ? account.providerAccountId
              : null
      });

      enrichedToken.appUserId = user.id;
      enrichedToken.onboardingCompleted = user.onboardingCompleted;
    }

    return enrichedToken;
  },
  async session({ session, token }) {
    if (session.user) {
      const enrichedToken = token as typeof token & {
        appUserId?: string;
        onboardingCompleted?: boolean;
      };

      session.user.id = typeof enrichedToken.appUserId === "string" ? enrichedToken.appUserId : "";
      session.user.onboardingCompleted = Boolean(enrichedToken.onboardingCompleted);
    }

    return session;
  },
  async signIn({ user }) {
    return Boolean(user.email);
  }
} satisfies NonNullable<NextAuthConfig["callbacks"]>;
