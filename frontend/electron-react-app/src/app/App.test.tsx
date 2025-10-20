import { render, screen } from "@testing-library/react";

import { App } from "./App";
import { AppProviders } from "./providers/AppProviders";
import { useAppStore } from "store/useAppStore";

test("renders analysis workspace shell", () => {
  useAppStore.setState((state) => ({
    ...state,
    auth: { ...state.auth, token: "test-token", username: "therapist" },
  }));

  render(
    <AppProviders>
      <App />
    </AppProviders>,
  );

  expect(
    screen.getByRole("heading", { name: /Therapy Compliance Analyzer/i }),
  ).toBeInTheDocument();
  expect(screen.getByRole("navigation")).toBeInTheDocument();
});
