import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/theme-provider";
import { QueryProvider } from "@/components/query-provider";
import { UserProvider } from "@/contexts/user-context";
import { env } from "@/lib/env";
import { CloudBackground } from "@/components/zyyn/cloud-background";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "zyyn",
  description: "create at the speed of thought",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <CloudBackground />
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <UserProvider>
              {children}
              <Toaster />
            </UserProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
