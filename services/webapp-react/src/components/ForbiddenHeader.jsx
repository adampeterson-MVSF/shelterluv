import PropTypes from 'prop-types';

/**
 * Header component for forbidden access state
 */
export function ForbiddenHeader({ handleLogout }) {
  return (
    <header className="app-header">
      <div className="header-content">
        <h1>Muttville</h1>
        <div className="unauthorized-message">
          <p>Access denied. Only @muttville.org accounts are permitted.</p>
          <button onClick={handleLogout}>Sign Out</button>
        </div>
      </div>
    </header>
  );
}

ForbiddenHeader.propTypes = {
  handleLogout: PropTypes.func.isRequired
};
