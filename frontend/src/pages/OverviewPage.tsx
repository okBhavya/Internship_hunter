import { useEffect, useState } from 'react';
import { api, type DashboardStats } from '../api';
import { Briefcase, Star, FileText, Send, Eye, TrendingUp, Building2, Target } from 'lucide-react';

export default function OverviewPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardStats().then(setStats).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  const kpis = stats ? [
    { label: 'Jobs Discovered', value: stats.jobs_discovered, icon: Briefcase, color: 'bg-blue-500' },
    { label: 'Jobs Matching', value: stats.jobs_matching, icon: Star, color: 'bg-yellow-500' },
    { label: 'Applications Prepared', value: stats.applications_prepared, icon: FileText, color: 'bg-purple-500' },
    { label: 'Applications Submitted', value: stats.applications_submitted, icon: Send, color: 'bg-green-500' },
    { label: 'Interviews', value: stats.interview_count, icon: Eye, color: 'bg-indigo-500' },
    { label: 'Avg Fit Score', value: `${stats.average_fit_score}%`, icon: Target, color: 'bg-pink-500' },
  ] : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl shadow-sm border p-4 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3">
              <div className={`${kpi.color} p-2 rounded-lg text-white`}>
                <kpi.icon size={20} />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
                <p className="text-xs text-gray-500">{kpi.label}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Response Rate */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="text-green-500" size={20} />
          <h3 className="font-semibold">Response Rate: {stats?.response_rate || 0}%</h3>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div className="bg-green-500 h-3 rounded-full transition-all" style={{ width: `${Math.min(stats?.response_rate || 0, 100)}%` }} />
        </div>
      </div>

      {/* Top Companies */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="text-blue-500" size={20} />
          <h3 className="font-semibold">Top Matching Companies</h3>
        </div>
        {stats?.top_companies?.length ? (
          <div className="space-y-3">
            {stats.top_companies.map((c, i) => (
              <div key={c.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono text-gray-400 w-6">{i + 1}.</span>
                  <span className="text-sm font-medium">{c.name}</span>
                </div>
                <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">{c.count} matches</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No matches yet. Run a discovery cycle to find jobs.</p>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => api.orchestrateDiscovery().then(() => window.location.reload())}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors"
          >
            🔍 Run Discovery
          </button>
          <a href="/jobs" className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium">
            Browse Jobs
          </a>
          <a href="/matches" className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium">
            View Top Matches
          </a>
          <a href="/profile" className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium">
            Update Profile
          </a>
        </div>
      </div>
    </div>
  );
}
