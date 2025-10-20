import { apiClient } from "../../lib/api/client";

export type ApiPreferences = {
  theme_mode: "system" | "light" | "dark";
  startup_screen: "analysis" | "dashboard" | "mission_control";
  enable_beta_widgets: boolean;
  auto_start_backend: boolean;
  stream_analysis_logs: boolean;
  default_strictness: "ultra_fast" | "balanced" | "thorough" | "clinical_grade";
  auto_export_format: "pdf" | "pdf_html";
};

export type PreferencesForm = {
  themeMode: ApiPreferences["theme_mode"];
  startupScreen: ApiPreferences["startup_screen"];
  enableBetaWidgets: boolean;
  autoStartBackend: boolean;
  streamAnalysisLogs: boolean;
  defaultStrictness: ApiPreferences["default_strictness"];
  autoExportFormat: ApiPreferences["auto_export_format"];
};

const mapFromApi = (preferences: ApiPreferences): PreferencesForm => ({
  themeMode: preferences.theme_mode,
  startupScreen: preferences.startup_screen,
  enableBetaWidgets: preferences.enable_beta_widgets,
  autoStartBackend: preferences.auto_start_backend,
  streamAnalysisLogs: preferences.stream_analysis_logs,
  defaultStrictness: preferences.default_strictness,
  autoExportFormat: preferences.auto_export_format,
});

const mapToApi = (preferences: PreferencesForm): ApiPreferences => ({
  theme_mode: preferences.themeMode,
  startup_screen: preferences.startupScreen,
  enable_beta_widgets: preferences.enableBetaWidgets,
  auto_start_backend: preferences.autoStartBackend,
  stream_analysis_logs: preferences.streamAnalysisLogs,
  default_strictness: preferences.defaultStrictness,
  auto_export_format: preferences.autoExportFormat,
});

export const fetchPreferences = async (): Promise<PreferencesForm> => {
  const { data } = await apiClient.get<ApiPreferences>("/preferences/me");
  return mapFromApi(data);
};

export const updatePreferences = async (
  preferences: PreferencesForm,
): Promise<PreferencesForm> => {
  const payload = mapToApi(preferences);
  const { data } = await apiClient.put<ApiPreferences>(
    "/preferences/me",
    payload,
  );
  return mapFromApi(data);
};
