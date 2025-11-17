import { useState, useEffect, useCallback } from 'react';
import { getDogs } from '../repositories/dogRepository';
import { useCancellableRequest, createRequestToken, checkRequestCancelled } from './useCancellableRequest';

/**
 * @typedef {Object} UseDogsReturn
 * @property {Array} allDogs - Array of normalized dog objects
 * @property {boolean} loading - Whether dogs are currently being fetched
 * @property {Error|null} error - Error if fetch failed, null otherwise
 * @property {function(): void} refetch - Function to manually trigger a fresh fetch
 */

/**
 * Custom hook for fetching dog data with request cancellation and race condition protection
 * @param {Object} authPermissions - Pure data about user permissions (not auth state)
 * @param {boolean} authPermissions.canViewDogs - Whether user can view dogs
 * @param {boolean} authPermissions.shouldHideDogs - Whether dogs should be hidden
 * @param {Object} options - Hook options
 * @param {boolean} options.autoFetch - Whether to fetch automatically on permission changes (default: true)
 * @returns {UseDogsReturn}
 */
export function useDogs(authPermissions, options = {}) {
  const { autoFetch = true } = options;
  const [allDogs, setAllDogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Track the current fetch request to prevent race conditions
  const requestRef = useCancellableRequest();

  const fetchDogs = useCallback(async () => {
    // Create new request token (cancels any previous request)
    const requestToken = createRequestToken(requestRef);

    setLoading(true);
    setError(null);

    try {
      const result = await getDogs();

      // Check if this request was cancelled
      if (checkRequestCancelled(requestToken, setLoading)) {
        return;
      }

      if (result.success) {
        setAllDogs(result.data);
        setError(null);
      } else {
        setError(result.error);
        setAllDogs([]);
      }
    } catch (err) {
      // Check if this request was cancelled
      if (checkRequestCancelled(requestToken, setLoading)) {
        return;
      }

      setError(err);
      setAllDogs([]);
    } finally {
      // Only clear loading if this is still the current request
      if (requestRef.current === requestToken) {
        setLoading(false);
      }
    }
  }, []);

  const refetch = useCallback(() => {
    fetchDogs();
  }, [fetchDogs]);

  // State machine for data fetching based on permissions
  useEffect(() => {
    if (!autoFetch) return;

    if (authPermissions.canViewDogs) {
      // Fetch fresh data when authenticated
      fetchDogs();
    } else if (authPermissions.shouldHideDogs) {
      // Clear stale data when not authenticated to prevent showing old data
      setAllDogs([]);
      setLoading(false);
      setError(null);
      // Cancel any in-flight request
      if (requestRef.current) {
        requestRef.current.cancelled = true;
      }
    }
    // 'loading' state: don't change data state
  }, [authPermissions.canViewDogs, authPermissions.shouldHideDogs, autoFetch, fetchDogs]);


  return {
    allDogs,
    loading,
    error,
    refetch
  };
}
