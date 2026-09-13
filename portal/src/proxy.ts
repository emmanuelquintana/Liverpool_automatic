import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const user = process.env.PORTAL_USER;
  const password = process.env.PORTAL_PASSWORD;
  if (!user || !password) return NextResponse.next();
  const auth = request.headers.get("authorization");
  if (auth?.startsWith("Basic ")) {
    const [suppliedUser, suppliedPassword] = atob(auth.slice(6)).split(":", 2);
    if (suppliedUser === user && suppliedPassword === password) return NextResponse.next();
  }
  return new NextResponse("Autenticación requerida", { status: 401, headers: { "WWW-Authenticate": 'Basic realm="Liverpool Seguimiento Goldval", charset="UTF-8"' } });
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
