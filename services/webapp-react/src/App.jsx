import { BrowserRouter as Router } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Header } from './components/Header';
import { RoutesConfig } from './RoutesConfig';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          <main>
            <RoutesConfig />
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
