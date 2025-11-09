import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import './styles/layout.css'
import './styles/header.css'
import './styles/home.css'
import './styles/dog-details.css'
import './styles/overlays.css'

// Initialize app services - validates config and sets up Firebase
// This happens once at app startup, not in module scope
import './app.js'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
