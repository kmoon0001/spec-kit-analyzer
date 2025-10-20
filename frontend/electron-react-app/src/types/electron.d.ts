// TypeScript declarations for Electron API
declare global {
  interface Window {
    electronAPI: {
      setSecureValue: (
        key: string,
        value: string,
      ) => Promise<{ success: boolean; error?: string }>;
      getSecureValue: (
        key: string,
      ) => Promise<{ success: boolean; value?: string; error?: string }>;
      removeSecureValue: (
        key: string,
      ) => Promise<{ success: boolean; error?: string }>;
      clearSecureStorage: () => Promise<{ success: boolean; error?: string }>;
    };
    desktopApi: {
      getEnvironment: () => Promise<{ isDev: boolean; apiBaseUrl: string }>;
      openExternal: (url: string) => void;
      platform: string;
      tasks: {
        startTask: (request: any) => Promise<any>;
        startAnalysis: (payload: any, options?: any) => Promise<any>;
        cancel: (jobId: string, reason?: string) => Promise<any>;
        list: () => Promise<any>;
        get: (jobId: string) => Promise<any>;
        on: (eventName: string, listener: (payload: any) => void) => () => void;
      };
      secureStorage: {
        setSecureValue: (
          key: string,
          value: string,
        ) => Promise<{ success: boolean; error?: string }>;
        getSecureValue: (
          key: string,
        ) => Promise<{ success: boolean; value?: string; error?: string }>;
        removeSecureValue: (
          key: string,
        ) => Promise<{ success: boolean; error?: string }>;
        clearSecureStorage: () => Promise<{ success: boolean; error?: string }>;
      };
      onDiagnostic: (listener: (payload: any) => void) => () => void;
    };
  }
}

export {};
