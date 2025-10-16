import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useEffect, useMemo } from 'react';
import { HashRouter } from 'react-router-dom';

import { useAppStore } from '../../store/useAppStore';
import '../../theme/global.css';

type Props = {
  children: ReactNode;
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const ThemeSynchronizer = ({ children }: Props) => {
  const theme = useAppStore((state) => state.theme.theme);

  useEffect(() => {
    document.body.dataset.theme = theme;
    document.body.style.backgroundColor =
      theme === 'dark' ? 'var(--color-bg-dark)' : 'var(--color-bg-light)';
    document.body.style.color =
      theme === 'dark' ? 'var(--color-text-dark)' : 'var(--color-text-light)';
  }, [theme]);

  return <>{children}</>;
};

export const AppProviders = ({ children }: Props) => {
  const router = useMemo(
    () => <HashRouter>{children}</HashRouter>,
    [children],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeSynchronizer>{router}</ThemeSynchronizer>
    </QueryClientProvider>
  );
};
