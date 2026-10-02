import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AppProvider } from "@/lib/state";
import { Shell } from "@/components/Shell";

export const metadata: Metadata = {
  title: "ARTHDARSHAN — Train before you face it",
  description: "An educational financial-decision-resilience simulator. No investment advice. No real money. Runs locally.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#0E1A33" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-simple="false">
      <body>
        <AppProvider>
          <Shell>{children}</Shell>
        </AppProvider>
      </body>
    </html>
  );
}
