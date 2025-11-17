import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { AUTH_STATE_KINDS } from '../contexts/AuthContext';
import { useAuthActions } from '../hooks/useAuthActions';
import { HeaderError } from './HeaderError';
import { ForbiddenHeader } from './ForbiddenHeader';
import { AuthControls } from './AuthControls';

/**
 * Main application header component
 */
export function Header() {
  const { authState } = useAuth();
  const { error, handleLogin, handleLogout } = useAuthActions();

  if (authState.kind === AUTH_STATE_KINDS.FORBIDDEN) {
    return <ForbiddenHeader handleLogout={handleLogout} />;
  }

  return (
    <header className="app-header">
      <div className="header-content">
        <Link to="/" className="app-title">
          <h1>Muttville <span className="font-normal">Senior Dogs</span></h1>
          <p className="app-header-subtitle">
            Give an older dog a second chance at happiness
          </p>
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
