import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
}

interface AuthState {
  token: string | null;
  username: string | null;
  setCredentials: (payload: { username: string; token: string }) => void;
  clear: () => void;
}

export interface AppState {
  theme: ThemeState;
  auth: AuthState;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: {
        theme: 'dark' as ThemeMode,
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
              theme: state.theme.theme === 'dark' ? 'light' : 'dark',
            },
          })),
      },
      auth: {
        token: null,
        username: null,
        setCredentials: ({ username, token }) =>
          set((state) => ({
            ...state,
            auth: {
              ...state.auth,
              username,
              token,
            },
          })),
        clear: () =>
          set((state) => ({
            ...state,
            auth: {
              ...state.auth,
              username: null,
              token: null,
            },
          })),
      },
    }),
    {
      name: 'tca-app-store',
      partialize: (state) => ({ auth: state.auth, theme: state.theme }),
    },
  ),
);
