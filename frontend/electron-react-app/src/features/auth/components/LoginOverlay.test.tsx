import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useAppStore } from '../../../store/useAppStore';
import * as authApi from '../api';
import { LoginOverlay } from './LoginOverlay';

const renderWithClient = (ui: React.ReactNode) => {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe('LoginOverlay', () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    useAppStore.setState((state) => ({
      ...state,
      auth: { ...state.auth, token: null, username: null },
    }));
  });

  it('stores credentials on successful login', async () => {
    jest.spyOn(authApi, 'login').mockResolvedValue({ access_token: 'test-token', token_type: 'bearer' });

    renderWithClient(<LoginOverlay />);

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'clinician' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'secret' } });
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(useAppStore.getState().auth.token).toBe('test-token'));
    expect(useAppStore.getState().auth.username).toBe('clinician');
  });

  it('shows error message if login fails', async () => {
    jest.spyOn(authApi, 'login').mockRejectedValue(new Error('Invalid credentials'));

    renderWithClient(<LoginOverlay />);

    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'clinician' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'bad-pass' } });
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument());
  });
});
