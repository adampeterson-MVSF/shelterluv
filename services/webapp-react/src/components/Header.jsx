import { useState } from 'react';
import PropTypes from 'prop-types';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

function HeaderError({ message }) {
  return <div className="error-message">{message}</div>;
}

HeaderError.propTypes = {
  message: PropTypes.string.isRequired
};

function ForbiddenHeader({ handleLogout }) {
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

function AuthControls({ authState, handleLogin, handleLogout }) {
  if (authState.kind === 'anonymous') {
    return (
      <button className="sign-in-btn" onClick={handleLogin}>
        Sign In
      </button>
    );
  }

  if (authState.kind === 'authenticated') {
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

export function Header() {
  const { authState, login, logout } = useAuth();
  const [error, setError] = useState(null);

  const handleLogin = async () => {
    setError(null);
    const result = await login();
    if (!result.success) {
      console.error('Login failed:', result.error);
      setError('Login failed. Please try again.');
    }
  };

  const handleLogout = async () => {
    setError(null);
    const result = await logout();
    if (!result.success) {
      console.error('Logout failed:', result.error);
      setError('Logout failed. Please try again.');
    }
  };

  if (authState.kind === 'forbidden') {
    return <ForbiddenHeader handleLogout={handleLogout} />;
  }

  return (
    <header className="app-header">
      <div className="header-content">
        <Link to="/" className="app-title">
          <h1>Muttville</h1>
        </Link>
        {error && <HeaderError message={error} />}
        <AuthControls
          authState={authState}
          handleLogin={handleLogin}
          handleLogout={handleLogout}
        />
      </div>
    </header>
  );
}
