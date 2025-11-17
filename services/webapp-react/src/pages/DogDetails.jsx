import { useParams } from 'react-router-dom';
import { useDogDetails } from '../hooks/useDogDetails';
import { AuthGate } from '../components/AuthGate';
import {
  LoadingState,
  DogNotFoundState,
  DogErrorState
} from '../components/PageStates';
import { DogDetailsLayout } from '../components/dog-details/DogDetailsLayout';

export default function DogDetails() {
  const { id } = useParams();
  const { dog, loading, error } = useDogDetails(id);
  const loadingFallback = <LoadingState message="Loading dog details..." />;

  let pageContent;

  if (loading) {
    pageContent = <LoadingState message="Loading dog details..." />;
  } else if (error) {
    pageContent =
      error.kind === 'not_found' ? (
        <DogNotFoundState />
      ) : (
        <DogErrorState error={error.message} />
      );
  } else if (!dog) {
    pageContent = <DogNotFoundState />;
  } else {
    pageContent = <DogDetailsLayout dog={dog} />;
  }

  return (
    <AuthGate loadingFallback={loadingFallback}>
      {pageContent}
    </AuthGate>
  );
}
