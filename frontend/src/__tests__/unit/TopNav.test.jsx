import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { TopNav } from '../../components/layout/TopNav';
import { AuthContext } from '../../context/auth-context';

test('renders TopNav component', () => {
  render(
    <AuthContext.Provider value={{ user: { name: 'Demo User' }, logout: () => {} }}>
      <BrowserRouter>
        <TopNav />
      </BrowserRouter>
    </AuthContext.Provider>
  );
  // Example assertion, checking if the logo/title exists
  expect(screen.getByText(/ReelForge/i)).toBeInTheDocument();
});
