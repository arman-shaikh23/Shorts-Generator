import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ApiDocsPage from '../../pages/ApiDocsPage';

test('navigates to ApiDocsPage and renders Swagger UI wrapper', () => {
  render(
    <MemoryRouter initialEntries={['/api-docs']}>
      <Routes>
        <Route path="/api-docs" element={<ApiDocsPage />} />
      </Routes>
    </MemoryRouter>
  );
  
  // Verify that the API Docs page renders its title
  expect(screen.getByText(/API Documentation/i)).toBeInTheDocument();
});
