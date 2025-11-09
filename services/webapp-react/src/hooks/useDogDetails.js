import { useState, useEffect } from 'react';
import { getDogById } from '../repositories/dogRepository';

/**
 * Custom hook for fetching a single dog by ID
 * Sets error state on failures instead of throwing
 * @param {string} id - Dog ID to fetch
 * @returns {Object} Hook state with dog, loading, and error
 */
export function useDogDetails(id) {
  const [dog, setDog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDog = async () => {
      setLoading(true);
      setError(null);

      if (!id) {
        setError('No dog ID provided');
        setLoading(false);
        return;
      }

      const result = await getDogById(id);
      if (result.success) {
        if (result.data) {
          setDog(result.data);
        } else {
          setError('Dog not found or has been adopted');
        }
      } else {
        console.error('Error fetching dog:', result.error);
        setError('Failed to load dog details');
      }
      setLoading(false);
    };

    fetchDog();
  }, [id]);

  return { dog, loading, error };
}
