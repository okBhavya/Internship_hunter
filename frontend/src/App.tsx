import { Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Briefcase, Star, FileText, Settings, Activity,
  Search, Upload, BarChart3, Bell, ChevronLeft, ChevronRight
} from 'lucide-react';
import { useState, useEffect } from 'react';
import OverviewPage from './pages/OverviewPage';
import JobsPage from './pages/JobsPage';
import TopMatchesPage from './pages/TopMatchesPage';
import ApplicationsPage from './pages/ApplicationsPage';
import ProfilesPage from './pages/ProfilesPage';
import SearchSettingsPage from './pages/SearchSettingsPage';
import AgentActivityPage from './pages/AgentActivityPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SourcesPage from './pages/SourcesPage';
import SetupPage from './pages/SetupPage';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/jobs', label: 'New Jobs', icon: Briefcase },
  { path: '/matches', label: 'Top Matches', icon: Star },
  { path: '/applications', label: 'Applications', icon: FileText },
  { path: '/profile', label: 'Resume/Profile', icon: Upload },
  { path: '/settings', label: 'Search Settings', icon: Settings },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/sources', label: 'Sources', icon: Search },
  { path: '/agents', label: 'Agent Activity', icon: Activity },
];

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const notifCount = 0;

  useEffect(() => {
    // Check if profile exists, redirect to setup if not
  }, []);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-gray-900 text-white transition-all duration-200 flex flex-col`}>
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          {sidebarOpen && <h1 className="text-lg font-bold">🎯 Internship Hunter</h1>}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-gray-400 hover:text-white">
            {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          </button>
        </div>
        <nav className="flex-1 py-4">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                location.pathname === item.path
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <item.icon size={18} />
              {sidebarOpen && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-700">
          {sidebarOpen && (
            <Link to="/setup" className="text-xs text-gray-400 hover:text-white block">
              ⚙️ Setup Wizard
            </Link>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {/* Top bar */}
        <header className="bg-white border-b px-6 py-3 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold text-gray-800">
              {navItems.find(n => n.path === location.pathname)?.label || 'Internship Hunter'}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <button className="relative text-gray-500 hover:text-gray-700">
              <Bell size={20} />
              {notifCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {notifCount}
                </span>
              )}
            </button>
          </div>
        </header>

        <div className="p-6">
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/matches" element={<TopMatchesPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/profile" element={<ProfilesPage />} />
            <Route path="/settings" element={<SearchSettingsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/agents" element={<AgentActivityPage />} />
            <Route path="/setup" element={<SetupPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default App;
