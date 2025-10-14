export {};

declare global {
  interface DesktopEnvironment {
    isDev: boolean;
    apiBaseUrl: string;
  }

  interface DesktopApi {
    getEnvironment: () => Promise<DesktopEnvironment>;
    openExternal: (url: string) => void;
    platform: NodeJS.Platform;
  }

  interface Window {
    desktopApi: DesktopApi;
  }
}
