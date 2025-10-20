import { create } from "zustand";
import { persist } from "zustand/middleware";
import { tokenManager } from "../lib/security/secureTokenStorage";

type ThemeMode = "light" | "dark";

interface ThemeState {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
}

interface AuthState {
  token: string | null;
  username: string | null;
  setCredentials: (payload: {
    username: string;
    token: string;
  }) => Promise<void>;
  clear: () => Promise<void>;
  isAuthenticated: () => Promise<boolean>;
}

export interface AppState {
  theme: ThemeState;
  auth: AuthState;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: {
        theme: "dark" as ThemeMode,
        setTheme: (theme) =>
          set((state) => ({
            ...state,
            theme: { ...state.theme, theme },
          })),
        toggleTheme: () =>
          set((state) => ({
            ...state,
            theme: {
              ...state.theme,
              theme: state.theme.theme === "dark" ? "light" : "dark",
            },
          })),
      },
      auth: {
        token: null,
        username: null,
        setCredentials: async ({ username, token }) => {
          // Store token securely
          await tokenManager.setAuthToken(token);

          set((state) => ({
            ...state,
            auth: {
              ...state.auth,
              username,
              token,
            },
          }));
        },
        clear: async () => {
          // Clear secure storage
          await tokenManager.clearAuthToken();

          set((state) => ({
            ...state,
            auth: {
              ...state.auth,
              username: null,
              token: null,
            },
          }));
        },
        isAuthenticated: async () => {
          return await tokenManager.isAuthenticated();
        },
      },
    }),
    {
      name: "tca-app-store",
      partialize: (state) => ({
        auth: {
          username: state.auth.username,
          token: null, // Don't persist token in localStorage, use secure storage
        },
        theme: state.theme,
      }),
    },
  ),
);
