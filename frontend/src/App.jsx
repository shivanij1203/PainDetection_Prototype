import { Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import VideoList from './pages/VideoList';
import AnnotationWorkspace from './pages/AnnotationWorkspace';
import QualityAnalyzer from './pages/QualityAnalyzer';
import './App.css';

function App() {
  return (
    <div className="app">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>NeoAnnotate</h1>
          <span className="subtitle">Neonatal Pain Annotation Tool</span>
        </div>
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
            Dashboard
          </NavLink>
          <NavLink to="/quality" className={({ isActive }) => isActive ? 'active' : ''}>
            Quality Analyzer
          </NavLink>
          <NavLink to="/videos" className={({ isActive }) => isActive ? 'active' : ''}>
            Videos
          </NavLink>
        </div>
      </nav>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/quality" element={<QualityAnalyzer />} />
          <Route path="/videos" element={<VideoList />} />
          <Route path="/annotate/:videoId" element={<AnnotationWorkspace />} />
        </Routes>
      </main>

      <footer className="footer">
        <p>Research Tool for Neonatal Pain Assessment | Addressing NICU Image Quality Challenges</p>
      </footer>
    </div>
  );
}

export default App;
