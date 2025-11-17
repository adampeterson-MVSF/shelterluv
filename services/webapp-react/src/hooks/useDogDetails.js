import { useState, useEffect } from 'react';
import { getDogById } from '../repositories/dogRepository';
import { useCancellableRequest, createRequestToken, checkRequestCancelled } from './useCancellableRequest';

/**
 * Processes the result from getDogById and returns processed state
 * @param {Object} result - Result from getDogById
 * @param {string} id - Dog ID
 * @returns {Object} Processed state with dog and error
 */
function processDogResult(result, id) {
  if (result.success) {
    if (result.data === null) {
      return {
        dog: null,
        error: { kind: 'not_found', message: `Dog with ID ${id} not found` }
      };
    } else {
      return { dog: result.data, error: null };
    }
  } else {
    // Repository already returns normalized error with kind
    return { dog: null, error: result.error };
  }
}

/**
 * Custom hook for fetching a single dog by ID with request cancellation
 * @param {string} id - Dog ID to fetch
 * @returns {Object} Hook state with dog, loading, and error
 */
export function useDogDetails(id) {
  const [dog, setDog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Track the current fetch request to prevent race conditions
  const requestRef = useCancellableRequest();

  useEffect(() => {
    if (!id) {
      setError({ kind: 'error', message: 'No dog ID provided' });
      setLoading(false);
      setDog(null);
      return;
    }

    // Create new request token (cancels any previous request)
    const requestToken = createRequestToken(requestRef);

    // Reset state for new fetch
    setLoading(true);
    setError(null);
    setDog(null);

    // Fetch data
    (async () => {
      try {
        const result = await getDogById(id);

        // Check if this request was cancelled
        if (checkRequestCancelled(requestToken, setLoading)) {
          return;
        }

        const { dog: newDog, error: newError } = processDogResult(result, id);
        setDog(newDog);
        setError(newError);

      } catch (err) {
        // Check if this request was cancelled
        if (checkRequestCancelled(requestToken, setLoading)) {
          return;
        }

        setError({ kind: 'error', message: err.message || 'Failed to fetch dog' });
        setDog(null);
      } finally {
        // Only clear loading if this is still the current request
        if (requestRef.current === requestToken) {
          setLoading(false);
        }
      }
    })();

  }, [id]);

  return { dog, loading, error };
}
