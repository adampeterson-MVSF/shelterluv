import { useRef, useEffect } from 'react';

/**
 * Hook that provides cancellation tokens for async operations.
 * Prevents race conditions when component re-renders or unmounts.
 *
 * @returns {Object} Object with { current: { cancelled: boolean } }
 */
export function useCancellableFetch() {
  const currentFetchRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (currentFetchRef.current) {
        currentFetchRef.current.cancelled = true;
      }
    };
  }, []);

  return currentFetchRef;
}

/**
 * Creates a new cancellation token and cancels any previous one.
 * Call this at the start of each async operation.
 *
 * @param {Object} fetchRef - The ref returned by useCancellableFetch
 * @returns {Object} Cancellation token { cancelled: boolean }
 */
export function createCancellationToken(fetchRef) {
  // Cancel any previous request
  if (fetchRef.current) {
    fetchRef.current.cancelled = true;
  }

  // Create new request token
  const requestToken = { cancelled: false };
  fetchRef.current = requestToken;

  return requestToken;
}

/**
 * Checks if a request token has been cancelled.
 * Call this during async operations to abort early.
 *
 * @param {Object} token - The cancellation token
 * @returns {boolean} True if the operation should be cancelled
 */
export function isCancelled(token) {
  return token.cancelled;
}
