// Test utilities - centralized test helpers, no global pollution
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';

/**
 * Render component with React Router wrapper.
 * @param {React.ReactElement} ui - Component to render
 * @param {Object} options - Render options
 * @returns {Object} Render result
 */
export function renderWithRouter(ui, options = {}) {
  const { ...renderOptions } = options;

  const wrapper = ({ children }) => (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );

  return render(ui, { wrapper, ...renderOptions });
}

/**
 * Render component with AuthProvider wrapper.
 * @param {React.ReactElement} ui - Component to render
 * @param {Object} options - Render options
 * @returns {Object} Render result
 */
export function renderWithAuth(ui, options = {}) {
  const { ...renderOptions } = options;

  const wrapper = ({ children }) => (
    <AuthProvider>
      {children}
    </AuthProvider>
  );

  return render(ui, { wrapper, ...renderOptions });
}

/**
 * Render component with both Router and AuthProvider wrappers.
 * @param {React.ReactElement} ui - Component to render
 * @param {Object} options - Render options
 * @returns {Object} Render result
 */
export function renderWithProviders(ui, options = {}) {
  const { ...renderOptions } = options;

  const wrapper = ({ children }) => (
    <BrowserRouter>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrowserRouter>
  );

  return render(ui, { wrapper, ...renderOptions });
}
