export { auth as proxy } from "@/auth";

export const config = {
  // Protect all routes - redirect unauthenticated users to /login
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico|login).*)"],
};
