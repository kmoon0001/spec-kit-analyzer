import "@testing-library/jest-dom";

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

jest.mock("axios", () => ({
  __esModule: true,
  default: mockAxios,
  ...mockAxios,
}));

const ensureCrypto = () => {
  const existing = global.crypto ?? ({} as Crypto);
  if (!existing.getRandomValues) {
    existing.getRandomValues = <T extends ArrayBufferView>(array: T): T => {
      const uint8Array = new Uint8Array(array.buffer, array.byteOffset, array.byteLength);
      for (let i = 0; i < uint8Array.length; i += 1) {
        uint8Array[i] = Math.floor(Math.random() * 256);
      }
      return array;
    };
  }
  if (!("randomUUID" in existing)) {
    (existing as any).randomUUID = jest.fn(() => "test-uuid");
  }
  const subtle = existing.subtle ?? ({} as SubtleCrypto);
  if (!subtle.importKey) {
    subtle.importKey = jest.fn(async () => ({} as CryptoKey)) as typeof subtle.importKey;
  }
  if (!subtle.encrypt) {
    subtle.encrypt = jest.fn(
      async () => new ArrayBuffer(16),
    ) as typeof subtle.encrypt;
  }
  if (!subtle.decrypt) {
    subtle.decrypt = jest.fn(
      async () => new ArrayBuffer(16),
    ) as typeof subtle.decrypt;
  }
  if (!subtle.digest) {
    subtle.digest = jest.fn(
      async () => new ArrayBuffer(16),
    ) as typeof subtle.digest;
  }
  Object.assign(existing, { subtle });
  Object.defineProperty(global, "crypto", {
    configurable: true,
    value: existing,
  });
};

ensureCrypto();

jest.mock("lib/security/secureTokenStorage", () => {
  const actual = jest.requireActual("lib/security/secureTokenStorage");
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
