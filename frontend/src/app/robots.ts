import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/dashboard/", "/api/", "/login"],
      },
      {
        userAgent: "GPTBot",
        allow: "/",
        disallow: ["/dashboard/", "/api/"],
      },
      {
        userAgent: "ClaudeBot",
        allow: "/",
        disallow: ["/dashboard/", "/api/"],
      },
      {
        userAgent: "PerplexityBot",
        allow: "/",
        disallow: ["/dashboard/", "/api/"],
      },
    ],
    sitemap: "https://skillpack.dev/sitemap.xml",
    host: "https://skillpack.dev",
  };
}
