import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { authCallbacks } from "./auth-callbacks";
import { env } from "./env";

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
  callbacks: authCallbacks
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
