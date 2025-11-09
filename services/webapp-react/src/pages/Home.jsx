import PropTypes from 'prop-types';
import { useDogs } from '../hooks/useDogs';
import { useAuth } from '../contexts/AuthContext';
import { DogCard } from '../components/DogCard';

function LoadingState() {
  return (
    <div className="page-container">
      <div className="loading">Loading...</div>
    </div>
  );
}

function AnonymousState() {
  return (
    <div className="page-container">
      <div className="login-prompt">
        <h2>Welcome to Muttville</h2>
        <p>Please sign in to view our dogs.</p>
      </div>
    </div>
  );
}

function ForbiddenState() {
  return (
    <div className="page-container">
      <div className="error-message">
        <h2>Access Denied</h2>
        <p>Only @muttville.org accounts are permitted to access this application.</p>
      </div>
    </div>
  );
}

function LoadingDogsState() {
  return (
    <div className="page-container">
      <div className="loading">Loading dogs...</div>
    </div>
  );
}

function ErrorState({ error }) {
  return (
    <div className="page-container">
      <div className="error-message">
        <h2>Error Loading Dogs</h2>
        <p>{error}</p>
        <p>Please try refreshing the page.</p>
      </div>
    </div>
  );
}

ErrorState.propTypes = {
  error: PropTypes.string.isRequired
};

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
  if (error) return <ErrorState error={error} />;

  if (loading) return <LoadingDogsState />;

  // Main content - simple list, no complex filtering/sorting
  return <DogList allDogs={allDogs} />;
}

export default Home;
