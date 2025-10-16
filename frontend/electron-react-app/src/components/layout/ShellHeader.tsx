import { Button } from '../ui/Button';
import { useAppStore } from '../../store/useAppStore';

import styles from './ShellHeader.module.css';

export const ShellHeader = () => {
  const theme = useAppStore((state) => state.theme.theme);
  const toggleTheme = useAppStore((state) => state.theme.toggleTheme);
  const username = useAppStore((state) => state.auth.username);
  const clearAuth = useAppStore((state) => state.auth.clear);

  return (
    <header className={styles.header}>
      <div className={styles.branding}>
        <span className={styles.logo}>TCA</span>
        <div>
          <h1 className={styles.title}>Therapy Compliance Analyzer</h1>
          <p className={styles.subtitle}>Clinical documentation review - Medicare compliance intelligence</p>
        </div>
      </div>
      <div className={styles.controls}>
        {username && <span className={styles.userBadge}>Signed in as {username}</span>}
        <Button variant="outline" onClick={toggleTheme}>
          {theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
        </Button>
        <Button variant="ghost" onClick={clearAuth}>
          Log Out
        </Button>
      </div>
    </header>
  );
};
