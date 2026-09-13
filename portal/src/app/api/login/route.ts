import { NextResponse } from "next/server";
import { createSession, SESSION_COOKIE, sessionCookieOptions } from "@/lib/session";

async function safeEqual(left: string, right: string) {
  const [a, b] = await Promise.all([left, right].map((value) => crypto.subtle.digest("SHA-256", new TextEncoder().encode(value))));
  return new Uint8Array(a).every((value, index) => value === new Uint8Array(b)[index]);
}

export async function POST(request: Request) {
  const form = await request.formData();
  const username = String(form.get("username") ?? "");
  const password = String(form.get("password") ?? "");
  const expectedUser = process.env.PORTAL_USER;
  const expectedPassword = process.env.PORTAL_PASSWORD;
  const secret = process.env.PORTAL_TOKEN ?? expectedPassword;
  const requestedNext = String(form.get("next") ?? "/");
  const next = requestedNext.startsWith("/") && !requestedNext.startsWith("//") && !requestedNext.startsWith("/login") ? requestedNext : "/";

  if (!expectedUser || !expectedPassword || !secret) {
    return NextResponse.redirect(new URL("/login?error=config", request.url), 303);
  }
  if (!(await safeEqual(username, expectedUser)) || !(await safeEqual(password, expectedPassword))) {
    const failure = new URL("/login", request.url);
    failure.searchParams.set("error", "credentials");
    if (next !== "/") failure.searchParams.set("next", next);
    return NextResponse.redirect(failure, 303);
  }

  const response = NextResponse.redirect(new URL(next, request.url), 303);
  response.cookies.set(SESSION_COOKIE, await createSession(username, secret), sessionCookieOptions);
  response.headers.set("Cache-Control", "no-store");
  return response;
}
