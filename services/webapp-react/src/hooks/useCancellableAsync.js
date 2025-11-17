import { useRef, useCallback, useEffect } from 'react';

/**
 * Hook for cancellable async operations with race condition protection.
 * Prevents stale data from overwriting fresh data when requests complete out of order.
 *
 * @returns {Object} Hook utilities
 * @property {function(Function): Promise} executeAsync - Execute an async function with cancellation support
 * @property {function(): void} cancel - Cancel the current operation
 */
export function useCancellableAsync() {
  const currentRequestRef = useRef(null);

  /**
   * Execute an async function with automatic cancellation of previous requests.
   * @param {Function} asyncFn - The async function to execute
   * @returns {Promise} Promise that resolves with the function result or rejects if cancelled
   */
  const executeAsync = useCallback(async (asyncFn) => {
    // Cancel any previous request
    if (currentRequestRef.current) {
      currentRequestRef.current.cancelled = true;
    }

    // Create new request token
    const requestToken = { cancelled: false };
    currentRequestRef.current = requestToken;

    try {
      const result = await asyncFn();

      // Check if this request was cancelled
      if (requestToken.cancelled) {
        throw new Error('Request was cancelled');
      }

      return result;
    } catch (error) {
      // Re-throw if cancelled (caller should handle silently)
      if (requestToken.cancelled) {
        throw new Error('Request was cancelled');
      }
      throw error;
    }
  }, []);

  /**
   * Cancel the current operation.
   */
  const cancel = useCallback(() => {
    if (currentRequestRef.current) {
      currentRequestRef.current.cancelled = true;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (currentRequestRef.current) {
        currentRequestRef.current.cancelled = true;
      }
    };
  }, []);

  return { executeAsync, cancel };
}
