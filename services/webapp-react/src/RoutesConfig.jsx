import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import DogDetails from './pages/DogDetails';

/**
 * Application routes configuration.
 * Extracted for testability - can be tested independently of App component.
 */
export function RoutesConfig() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dog/:id" element={<DogDetails />} />
    </Routes>
  );
}
