import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

/**
 * Shared page state components for consistent loading, error, and empty states
 */

export function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="page-container">
      <div className="loading">{message}</div>
    </div>
  );
}

LoadingState.propTypes = {
  message: PropTypes.string
};

export function AnonymousState() {
  return (
    <div className="page-container">
      <div className="login-prompt">
        <h2>Welcome to Muttville</h2>
        <p>Please sign in to view our dogs.</p>
      </div>
    </div>
  );
}

export function ForbiddenState() {
  return (
    <div className="page-container">
      <div className="error-message">
        <h2>Access Denied</h2>
        <p>Only @muttville.org accounts are permitted to access this application.</p>
      </div>
    </div>
  );
}

export function LoadingDogsState() {
  return (
    <div className="page-container">
      <div className="loading">Loading dogs...</div>
    </div>
  );
}

export function ErrorState({ error, title = 'Error', backLink = '/', backText = 'Go back' }) {
  return (
    <div className="page-container">
      <div className="error-message">
        <h2>{title}</h2>
        <p>{error}</p>
        <Link to={backLink} className="btn-primary">{backText}</Link>
      </div>
    </div>
  );
}

ErrorState.propTypes = {
  error: PropTypes.string.isRequired,
  title: PropTypes.string,
  backLink: PropTypes.string,
  backText: PropTypes.string
};

export function NotFoundState({ message = 'Item not found', backLink = '/', backText = 'Go back' }) {
  return (
    <div className="page-container">
      <div className="error-message">
        <h2>{message}</h2>
        <p>This item may no longer be available.</p>
        <Link to={backLink} className="btn-primary">{backText}</Link>
      </div>
    </div>
  );
}

NotFoundState.propTypes = {
  message: PropTypes.string,
  backLink: PropTypes.string,
  backText: PropTypes.string
};

export function DogNotFoundState() {
  return (
    <div className="page-container dog-details-page">
      <Link to="/" className="back-link">← Back to all dogs</Link>
      <div className="error-state">
        <h2>Dog not found</h2>
        <p>This dog may have been adopted or the information is no longer available.</p>
        <Link to="/" className="btn-primary">View all dogs</Link>
      </div>
    </div>
  );
}

export function DogErrorState({ error }) {
  return (
    <div className="page-container dog-details-page">
      <Link to="/" className="back-link">← Back to all dogs</Link>
      <div className="error-state">
        <h2>Unable to load dog</h2>
        <p>{error}</p>
        <Link to="/" className="btn-primary">View all dogs</Link>
      </div>
    </div>
  );
}

DogErrorState.propTypes = {
  error: PropTypes.string.isRequired
};
