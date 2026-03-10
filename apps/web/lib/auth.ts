import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { env } from "./env";
import { ensureUserRecord, getUserByEmail } from "./queries";

export const { handlers, auth } = NextAuth({
  secret: env.nextAuthSecret,
  session: {
    strategy: "jwt"
  },
  providers: [
    Google({
      clientId: env.googleClientId,
      clientSecret: env.googleClientSecret
    })
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      const enrichedToken = token as typeof token & {
        appUserId?: string;
        onboardingCompleted?: boolean;
      };

      if (token.email) {
        const user = await ensureUserRecord({
          email: token.email,
          name: typeof token.name === "string" ? token.name : null,
          image: typeof token.picture === "string" ? token.picture : null,
          providerSubject:
            typeof profile?.sub === "string"
              ? profile.sub
              : typeof account?.providerAccountId === "string"
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
      if (!user.email) {
        return false;
      }

      const existing = await getUserByEmail(user.email);
      if (!existing) {
        await ensureUserRecord({
          email: user.email,
          name: user.name ?? null,
          image: user.image ?? null,
          providerSubject: null
        });
      }

      return true;
    }
  }
});

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
      onboardingCompleted?: boolean;
    };
  }
}
