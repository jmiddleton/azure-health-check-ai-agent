"use client";

import { useEffect } from "react";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const updateTheme = () => {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const html = document.documentElement;
      
      if (isDark) {
        html.classList.add("dark");
      } else {
        html.classList.remove("dark");
      }
    };

    // Set initial theme
    updateTheme();

    // Listen for changes
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", updateTheme);

    return () => {
      mediaQuery.removeEventListener("change", updateTheme);
    };
  }, []);

  return <>{children}</>;
}

