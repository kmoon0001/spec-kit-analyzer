import { MainLayout } from "../components/layout/MainLayout";
import { AuthGate } from "../features/auth/components/AuthGate";
import { AppRouter } from "./router/AppRouter";

export const App = () => {
  return (
    <AuthGate>
      <MainLayout>
        <AppRouter />
      </MainLayout>
    </AuthGate>
  );
};
