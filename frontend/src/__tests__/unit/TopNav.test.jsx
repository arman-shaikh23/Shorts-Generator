import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { TopNav } from '../../components/layout/TopNav';

test('renders TopNav component', () => {
  render(
    <BrowserRouter>
      <TopNav />
    </BrowserRouter>
  );
  // Example assertion, checking if the logo/title exists
  expect(screen.getByText(/ReelForge/i)).toBeInTheDocument();
});
