export { auth as proxy } from "@/auth";

export const config = {
  // Protect all routes except home (landing), login, and NextAuth internals
  matcher: ["/explore/:path*", "/bundle/:path*", "/skills/:path*", "/dashboard/:path*"],
};
