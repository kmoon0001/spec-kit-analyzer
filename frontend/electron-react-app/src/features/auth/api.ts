import { apiClient } from '../../lib/api/client';

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export const login = async (username: string, password: string): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  formData.append('grant_type', 'password');

  const { data } = await apiClient.post<TokenResponse>('/auth/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data;
};
