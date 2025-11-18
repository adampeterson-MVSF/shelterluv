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

  // Compute pure permission data from auth state
  const authPermissions = {
    canViewDogs: authState.kind === 'authenticated',
    shouldHideDogs: authState.kind === 'anonymous' || authState.kind === 'forbidden'
  };

  const { allDogs, loading, error } = useDogs(authPermissions);

  if (error) {
    const errorMessage = error?.message || error?.toString() || 'An error occurred loading dogs';
    return (
      <AuthGate>
        <ErrorState error={errorMessage} title="Error Loading Dogs" backText="Try refreshing" />
      </AuthGate>
    );
  }

  if (loading) {
    return (
      <AuthGate>
        <LoadingDogsState />
      </AuthGate>
    );
  }

  return (
    <AuthGate>
      <DogList allDogs={allDogs} />
    </AuthGate>
  );
}

export default Home;
