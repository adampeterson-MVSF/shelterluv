import PropTypes from 'prop-types';
import { useDogs } from '../hooks/useDogs';
import { useAuth } from '../contexts/AuthContext';
import { DogCard } from '../components/DogCard';
import { AuthGate } from '../components/AuthGate';
import {
  LoadingDogsState,
  ErrorState
} from '../components/PageStates';

function DogList({ allDogs }) {
  return (
    <div className="page-container home-page">
      <div className="page-header">
        <h1>Dogs</h1>
        <p className="results-count">
          {allDogs.length} {allDogs.length === 1 ? 'dog' : 'dogs'}
        </p>
      </div>

      <div className="dogs-grid">
        {allDogs.map(dog => <DogCard key={dog.id} dog={dog} />)}
      </div>
    </div>
  );
}

DogList.propTypes = {
  allDogs: PropTypes.array.isRequired
};

/**
 * Home page component - displays dogs in a simple list
 * No filtering, sorting, or search - keep it simple per constraints
 * @returns {JSX.Element} Home component
 */
function Home() {
  const { authState } = useAuth();
  const { allDogs, loading, error } = useDogs(authState);

  // Auth states - fail loud on errors
  if (authState.kind === 'loading') return <LoadingState />;
  if (authState.kind === 'anonymous') return <AnonymousState />;
  if (authState.kind === 'forbidden') return <ForbiddenState />;

  // Show error state instead of throwing
  if (error) return <ErrorState error={error} title="Error Loading Dogs" backText="Try refreshing" />;

  if (loading) return <LoadingDogsState />;

  // Main content - simple list, no complex filtering/sorting
  return <DogList allDogs={allDogs} />;
}

export default Home;
