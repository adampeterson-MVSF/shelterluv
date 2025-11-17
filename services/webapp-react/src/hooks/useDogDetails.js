import { useState, useEffect, useRef } from 'react';
import { getDogById } from '../repositories/dogRepository';
import { DOG_ERROR_CODES } from '../types/dogErrors';

/**
 * Custom hook for fetching a single dog by ID
 * @param {string} id - Dog ID to fetch
 * @returns {Object} Hook state with dog, loading, and error
 */
export function useDogDetails(id) {
  const [dog, setDog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isMountedRef = useRef(true);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!id) {
      setError({ message: 'No dog ID provided' });
      setLoading(false);
      return;
    }

    const fetchDog = async () => {
      if (!isMountedRef.current) return;

      setLoading(true);
      setError(null);
      setDog(null);

      console.log('[useDogDetails] Fetching dog with ID:', id);

      try {
        const result = await getDogById(id);
        
        // 🔍 BREAKPOINT TARGET: Inspect `result` here
        // Expected: { success: true, data: {...normalizedDog} } or { success: false, error: {...} }
        console.log('🔍 [useDogDetails] BREAKPOINT CHECKPOINT - Result received:', {
          success: result?.success,
          hasData: !!result?.data,
          hasError: !!result?.error,
          dataType: typeof result?.data,
          resultKeys: result ? Object.keys(result) : [],
          dataKeys: result?.data ? Object.keys(result.data).slice(0, 5) : [],
          result: result // Full object for inspection
        });

        if (!isMountedRef.current) {
          console.warn('[useDogDetails] Component unmounted, skipping state update');
          return;
        }

        console.log('[useDogDetails] Component still mounted, processing result');
        
        if (result.success) {
          if (result.data === null) {
            // Document doesn't exist - treat as not_found error
            console.log('[useDogDetails] Document not found, setting error');
            setError({ kind: 'not_found', message: `Dog with ID ${id} not found` });
          } else {
            // 🔍 BREAKPOINT TARGET: Inspect before setDog
            console.log('🔍 [useDogDetails] About to call setDog with:', {
              dogName: result.data?.Name,
              dogId: result.data?.id,
              dogKeys: Object.keys(result.data).slice(0, 10),
              fullData: result.data
            });
            setDog(result.data);
            console.log('✅ [useDogDetails] setDog called successfully');
          }
        } else {
          console.error('[useDogDetails] Error fetching dog:', result.error);
          // Convert DogError to expected format
          const errorObj = result.error?.code === DOG_ERROR_CODES.DOCUMENT_NOT_FOUND
            ? { kind: 'not_found', message: result.error.message }
            : { kind: 'error', message: result.error?.message || 'Unknown error' };
          setError(errorObj);
        }
      } catch (err) {
        console.error('[useDogDetails] Unexpected error:', err);
        setError({ kind: 'error', message: err.message || 'Failed to fetch dog' });
      } finally {
        console.log('[useDogDetails] Setting loading to false');
        setLoading(false);
      }
    };

    fetchDog();
  }, [id]);

  return { dog, loading, error };
}
