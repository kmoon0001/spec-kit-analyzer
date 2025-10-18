import { Sun, Moon, LogOut, Activity } from 'lucide-react';
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
        <div className={styles.logoContainer}>
          <Activity className={styles.logoIcon} size={28} strokeWidth={2.5} />
          <span className={styles.logo}>TCA</span>
        </div>
        <div>
          <h1 className={styles.title}>Therapy Compliance Analyzer</h1>
          <p className={styles.subtitle}>Clinical documentation review • Medicare compliance intelligence</p>
        </div>
      </div>
      <div className={styles.controls}>
        {username && (
          <span className={styles.userBadge}>
            <span className={styles.userDot} />
            {username}
          </span>
        )}
        <Button variant="outline" onClick={toggleTheme} title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          <span className={styles.buttonText}>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </Button>
        <Button variant="ghost" onClick={clearAuth} title="Log Out">
          <LogOut size={16} />
          <span className={styles.buttonText}>Log Out</span>
        </Button>
      </div>
    </header>
  );
};
