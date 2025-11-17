import PropTypes from 'prop-types';
import { AUTH_STATE_KINDS } from '../contexts/AuthContext';

/**
 * Authentication control buttons component
 */
export function AuthControls({ authState, handleLogin, handleLogout }) {
  if (authState.kind === AUTH_STATE_KINDS.ANONYMOUS) {
    return (
      <button className="sign-in-btn" onClick={handleLogin}>
        Sign In
      </button>
    );
  }

  if (authState.kind === AUTH_STATE_KINDS.AUTHENTICATED) {
    return (
      <div className="header-user-section">
        <span className="user-info">{authState.user.email}</span>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>
    );
  }

  return null;
}

AuthControls.propTypes = {
  authState: PropTypes.object.isRequired,
  handleLogin: PropTypes.func.isRequired,
  handleLogout: PropTypes.func.isRequired
};
