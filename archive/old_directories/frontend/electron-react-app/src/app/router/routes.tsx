import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

const AnalysisPage = lazy(() => import('../../features/analysis/pages/AnalysisPage'));
const DashboardPage = lazy(() => import('../../features/dashboard/pages/DashboardPage'));
const MissionControlPage = lazy(() => import('../../features/mission-control/pages/MissionControlPage'));
const SettingsPage = lazy(() => import('../../features/settings/pages/SettingsPage'));

export const appRoutes: RouteObject[] = [
  {
    path: '/',
    element: <AnalysisPage />,
  },
  {
    path: '/dashboard',
    element: <DashboardPage />,
  },
  {
    path: '/mission-control',
    element: <MissionControlPage />,
  },
  {
    path: '/settings',
    element: <SettingsPage />,
  },
];
