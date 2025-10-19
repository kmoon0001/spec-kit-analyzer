import { FormEvent, useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { Button } from '../../../components/ui/Button';
import { Card } from '../../../components/ui/Card';
import { login } from '../api';
import { useAppStore } from '../../../store/useAppStore';

import styles from './LoginOverlay.module.css';

export const LoginOverlay = () => {
  const setCredentials = useAppStore((state) => state.auth.setCredentials);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => login(username, password),
    onSuccess: async (data) => {
      await setCredentials({ username, token: data.access_token });
      setError(null);
      setPassword('');
    },
    onError: (err) => {
      const message = err instanceof Error ? err.message : 'Unable to authenticate.';
      setError(message);
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <div className={styles.overlay}>
      <Card title="Secure Login" subtitle="Authenticate to access the compliance analyzer">
        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.label}>
            Username
            <input
              className={styles.input}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label className={styles.label}>
            Password
            <input
              className={styles.input}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <p className={styles.error}>{error}</p>}
          <div style={{ display: 'flex', gap: '8px', flexDirection: 'column' }}>
            <Button type="submit" variant="primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Signing in...' : 'Sign In'}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={async () => {
                const clear = useAppStore.getState().auth.clear;
                await clear();
                localStorage.removeItem('tca-app-store');
                window.location.reload();
              }}
              style={{ fontSize: '0.8rem', padding: '4px 8px' }}
            >
              Clear Stored Data & Refresh
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
