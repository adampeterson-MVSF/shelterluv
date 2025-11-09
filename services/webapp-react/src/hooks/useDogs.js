import { useState, useEffect, useCallback } from 'react';
import { getDogs } from '../repositories/dogRepository';

/**
 * @typedef {Object} UseDogsReturn
 * @property {Array} allDogs - Array of normalized dog objects
 * @property {boolean} loading - Whether dogs are currently being fetched
 * @property {Error|null} error - Error if fetch failed, null otherwise
 * @property {function(): void} refetch - Function to manually trigger a fresh fetch
 */

/**
 * Custom hook for fetching dog data
 * Fetches all dogs once when authenticated, sets error state on failures
 * @param {Object} authState - Authentication state from useAuth hook
 * @param {string} authState.kind - Current auth kind ('loading'|'authenticated'|'anonymous'|'forbidden')
 * @returns {UseDogsReturn}
 */
export function useDogs(authState) {
  const [allDogs, setAllDogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Check for test data override (for e2e testing)
  const testDogs = (typeof window !== 'undefined' && window.TEST_DOG_DATA) ||
                   (typeof localStorage !== 'undefined' && localStorage.getItem('TEST_DOG_DATA') && JSON.parse(localStorage.getItem('TEST_DOG_DATA')));
  if (testDogs) {
    return {
      allDogs: testDogs,
      loading: false,
      error: null,
      refetch: () => {}
    };
  }

  const fetchDogs = useCallback(async () => {
    setLoading(true);
    setError(null);

    const result = await getDogs();
    if (result.success) {
      setAllDogs(result.data);
    } else {
      console.error('Error fetching dogs:', result.error);
      setError(result.error);
      setAllDogs([]);
    }
    setLoading(false);
  }, []);

  const refetch = useCallback(() => {
    fetchDogs();
  }, [fetchDogs]);

  useEffect(() => {
    // Only fetch dogs when user is authenticated
    if (authState.kind === 'authenticated') {
      fetchDogs();
    } else if (authState.kind === 'anonymous' || authState.kind === 'forbidden') {
      // Clear any existing data and errors when not authenticated
      setAllDogs([]);
      setLoading(false);
      setError(null);
    }
  }, [authState.kind, fetchDogs]);

  return {
    allDogs,
    loading,
    error,
    refetch
  };
}
