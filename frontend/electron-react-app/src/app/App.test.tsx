import { render, screen } from '@testing-library/react';

import { App } from './App';
import { AppProviders } from './providers/AppProviders';

test('renders analysis workspace placeholder', () => {
  render(
    <AppProviders>
      <App />
    </AppProviders>,
  );
  expect(screen.getByText(/Analysis Workspace/i)).toBeInTheDocument();
});
