import '@testing-library/jest-dom';

const mockAxiosInstance = {
  defaults: {},
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() },
  },
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  patch: jest.fn(),
  head: jest.fn(),
  options: jest.fn(),
  request: jest.fn(),
};

const mockAxios = {
  create: jest.fn(() => mockAxiosInstance),
  isCancel: jest.fn(() => false),
  CancelToken: { source: jest.fn(() => ({ token: {}, cancel: jest.fn() })) },
};

jest.mock('axios', () => ({
  __esModule: true,
  default: mockAxios,
  ...mockAxios,
}));

const ensureCrypto = () => {
  const existing = global.crypto ?? ({} as Crypto);
  if (!existing.getRandomValues) {
    existing.getRandomValues = (array: Uint8Array) => {
      for (let i = 0; i < array.length; i += 1) {
        array[i] = Math.floor(Math.random() * 256);
      }
      return array;
    };
  }
  if (!('randomUUID' in existing)) {
    existing.randomUUID = jest.fn(() => 'test-uuid') as unknown as () => string;
  }
  const subtle = existing.subtle ?? ({} as SubtleCrypto);
  if (!subtle.importKey) {
    subtle.importKey = jest.fn(async () => ({})) as typeof subtle.importKey;
  }
  if (!subtle.encrypt) {
    subtle.encrypt = jest.fn(async () => new ArrayBuffer(16)) as typeof subtle.encrypt;
  }
  if (!subtle.decrypt) {
    subtle.decrypt = jest.fn(async () => new ArrayBuffer(16)) as typeof subtle.decrypt;
  }
  if (!subtle.digest) {
    subtle.digest = jest.fn(async () => new ArrayBuffer(16)) as typeof subtle.digest;
  }
  existing.subtle = subtle;
  Object.defineProperty(global, 'crypto', {
    configurable: true,
    value: existing,
  });
};

ensureCrypto();

jest.mock('lib/security/secureTokenStorage', () => {
  const actual = jest.requireActual('lib/security/secureTokenStorage');
  return {
    ...actual,
    tokenManager: {
      setAuthToken: jest.fn().mockResolvedValue(undefined),
      getAuthToken: jest.fn().mockResolvedValue(null),
      clearAuthToken: jest.fn().mockResolvedValue(undefined),
      clearAll: jest.fn().mockResolvedValue(undefined),
      isAuthenticated: jest.fn().mockResolvedValue(false),
    },
  };
});
