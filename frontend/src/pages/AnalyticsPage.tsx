import { useEffect, useState } from 'react';
import { api, type DashboardStats } from '../api';
import { BarChart3, TrendingUp } from 'lucide-react';

export default function AnalyticsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardStats().then(setStats).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  const barData = stats ? [
    { label: 'Discovered', value: stats.jobs_discovered, color: 'bg-blue-500' },
    { label: 'Matching', value: stats.jobs_matching, color: 'bg-green-500' },
    { label: 'Prepared', value: stats.applications_prepared, color: 'bg-purple-500' },
    { label: 'Submitted', value: stats.applications_submitted, color: 'bg-indigo-500' },
    { label: 'Interviews', value: stats.interview_count, color: 'bg-yellow-500' },
  ] : [];

  const maxVal = Math.max(...barData.map(d => d.value), 1);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>

      {/* Pipeline Bar Chart */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold flex items-center gap-2 mb-4"><BarChart3 size={18} /> Application Pipeline</h3>
        <div className="space-y-3">
          {barData.map(d => (
            <div key={d.label} className="flex items-center gap-4">
              <span className="text-sm text-gray-600 w-24">{d.label}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
                <div className={`${d.color} h-full rounded-full transition-all flex items-center pl-3`}
                  style={{ width: `${Math.max((d.value / maxVal) * 100, d.value > 0 ? 8 : 0)}%` }}>
                  <span className="text-xs text-white font-medium">{d.value}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-blue-600">{stats?.average_fit_score || 0}%</p>
          <p className="text-sm text-gray-500 mt-1">Avg Fit Score</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-green-600">{stats?.response_rate || 0}%</p>
          <p className="text-sm text-gray-500 mt-1">Response Rate</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-purple-600">
            {stats?.jobs_matching && stats?.jobs_discovered ? Math.round((stats.jobs_matching / Math.max(stats.jobs_discovered, 1)) * 100) : 0}%
          </p>
          <p className="text-sm text-gray-500 mt-1">Match Rate</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4 text-center">
          <p className="text-3xl font-bold text-indigo-600">{stats?.top_companies?.length || 0}</p>
          <p className="text-sm text-gray-500 mt-1">Companies</p>
        </div>
      </div>

      {/* Top Companies */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold flex items-center gap-2 mb-4"><TrendingUp size={18} /> Top Companies by Matches</h3>
        {stats?.top_companies?.length ? (
          <div className="space-y-2">
            {stats.top_companies.map((c, i) => (
              <div key={c.name} className="flex items-center gap-3">
                <span className="text-sm font-mono text-gray-400 w-6">#{i + 1}</span>
                <span className="text-sm font-medium flex-1">{c.name}</span>
                <div className="w-32 bg-gray-100 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(c.count / Math.max(stats.top_companies[0].count, 1)) * 100}%` }} />
                </div>
                <span className="text-sm text-gray-500 w-8 text-right">{c.count}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No data yet. Run discovery to populate analytics.</p>
        )}
      </div>
    </div>
  );
}
