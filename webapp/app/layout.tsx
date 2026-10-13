import type { Metadata, Viewport } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";
import Shell from "@/components/Shell";
import { DataProvider } from "@/lib/data";

export const metadata: Metadata = {
  title: "NodiNajar · Jamuna riverbank watch",
  description: "NISAR radar sees the Jamuna's banks through monsoon cloud. NodiNajar measures where the bank moves, ranks the stretches next to homes and drafts Bangla alerts.",
  icons: { icon: "/favicon.svg" },
};
export const viewport: Viewport = { themeColor: "#0b161d", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <DataProvider>
          <Shell>{children}</Shell>
        </DataProvider>
      </body>
    </html>
  );
}
