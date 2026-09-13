import { NextResponse, type NextRequest } from "next/server";
import { SESSION_COOKIE, verifySession } from "@/lib/session";

export async function proxy(request: NextRequest) {
  const user = process.env.PORTAL_USER;
  const password = process.env.PORTAL_PASSWORD;
  if (!user || !password) return NextResponse.next();
  if (request.nextUrl.pathname === "/login" || request.nextUrl.pathname === "/api/login") return NextResponse.next();
  const secret = process.env.PORTAL_TOKEN ?? password;
  if (await verifySession(request.cookies.get(SESSION_COOKIE)?.value, secret)) return NextResponse.next();
  const login = new URL("/login", request.url);
  if (request.nextUrl.pathname !== "/") login.searchParams.set("next", `${request.nextUrl.pathname}${request.nextUrl.search}`);
  return NextResponse.redirect(login);
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
