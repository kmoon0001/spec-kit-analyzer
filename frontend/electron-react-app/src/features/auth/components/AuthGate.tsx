import { ReactNode } from "react";

import { useAppStore } from "../../../store/useAppStore";
import { LoginOverlay } from "./LoginOverlay";

export const AuthGate = ({ children }: { children: ReactNode }) => {
  const token = useAppStore((state) => state.auth.token);

  return (
    <>
      {children}
      {!token && <LoginOverlay />}
    </>
  );
};
