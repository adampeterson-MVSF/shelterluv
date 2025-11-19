import { useState, useEffect, useCallback } from 'react';
import { getDogs } from '../repositories/dogRepository';

/**
 * @typedef {Object} UseDogsReturn
 * @property {Array} allDogs - Array of normalized dog objects
 * @property {boolean} loading - Whether dogs are currently being fetched
 * @property {Error|null} error - Error if fetch failed, null otherwise
 * @property {function(): void} refetch - Function to manually trigger a fresh fetch
 * @property {function(): void} loadMore - Function to load more dogs for pagination
 * @property {boolean} hasMore - Whether there are more dogs to load
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
  const [lastDoc, setLastDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);

  const fetchDogs = useCallback(async (signal, isLoadMore = false) => {
    setLoading(true);
    setError(null);

    try {
      const result = await getDogs(20, isLoadMore ? lastDoc : null, signal);

      if (result.success) {
        if (isLoadMore) {
          setAllDogs(prevDogs => [...prevDogs, ...result.data]);
        } else {
          setAllDogs(result.data);
        }
        setLastDoc(result.lastDoc);
        setHasMore(result.data.length === 20); // If we got less than limit, no more data
        setError(null);
      } else {
        setError(result.error);
        if (!isLoadMore) {
          setAllDogs([]);
        }
      }
    } catch (err) {
      setError(err);
      if (!isLoadMore) {
        setAllDogs([]);
      }
    } finally {
      setLoading(false);
    }
  }, [lastDoc]);

  const refetch = useCallback(() => {
    setLastDoc(null);
    setHasMore(true);
    const controller = new AbortController();
    fetchDogs(controller.signal);
  }, [fetchDogs]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      const controller = new AbortController();
      fetchDogs(controller.signal, true);
    }
  }, [fetchDogs, loading, hasMore]);

  // State machine for data fetching based on permissions
  useEffect(() => {
    if (!autoFetch) return;

    if (authPermissions.canViewDogs) {
      // Fetch fresh data when authenticated
      const controller = new AbortController();
      fetchDogs(controller.signal);

      // Cleanup: abort request on unmount or permission change
      return () => controller.abort();
    } else if (authPermissions.shouldHideDogs) {
      // Clear stale data when not authenticated to prevent showing old data
      setAllDogs([]);
      setLastDoc(null);
      setHasMore(true);
      setLoading(false);
      setError(null);
    }
    // 'loading' state: don't change data state
  }, [authPermissions.canViewDogs, authPermissions.shouldHideDogs, autoFetch]);


  return {
    allDogs,
    loading,
    error,
    refetch,
    loadMore,
    hasMore
  };
}
