import { useRef, useEffect } from 'react';

/**
 * Hook for managing cancellable async requests.
 * Provides a request token that can be used to check if the request should be cancelled.
 * Automatically cleans up on unmount.
 *
 * @returns {Object} Object with { current: { cancelled: boolean } } ref
 */
export function useCancellableRequest() {
  const requestRef = useRef({ cancelled: false });

  useEffect(() => {
    // Reset cancelled state on mount
    requestRef.current.cancelled = false;

    // Cleanup function to cancel any in-flight request on unmount
    return () => {
      requestRef.current.cancelled = true;
    };
  }, []);

  return requestRef;
}

/**
 * Helper to create a new request token and cancel any previous request.
 * @param {Object} requestRef - Ref returned by useCancellableRequest
 * @returns {Object} New request token { cancelled: false }
 */
export function createRequestToken(requestRef) {
  // Cancel any previous request
  if (requestRef.current) {
    requestRef.current.cancelled = true;
  }

  // Create new request token
  const requestToken = { cancelled: false };
  requestRef.current = requestToken;
  return requestToken;
}

/**
 * Check if a request should be cancelled and handle cleanup.
 * @param {Object} requestToken - Request token to check
 * @param {Function} setLoading - Function to call to set loading state to false
 * @returns {boolean} True if request was cancelled, false otherwise
 */
export function checkRequestCancelled(requestToken, setLoading) {
  if (requestToken.cancelled) {
    setLoading(false);
    return true;
  }
  return false;
}
