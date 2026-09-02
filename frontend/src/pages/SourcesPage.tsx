import { useEffect, useState } from 'react';
import { api } from '../api';
import { Search, Clock, CheckCircle } from 'lucide-react';

export default function SourcesPage() {
  const [sources, setSources] = useState<any[]>([]);
  const [available, setAvailable] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getSources().catch(() => []),
      fetch('/api/sources/available').then(r => r.json()).catch(() => []),
    ]).then(([s, a]) => { setSources(s); setAvailable(a); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Job Sources</h1>

      {/* Active Sources */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold flex items-center gap-2 mb-4"><Search size={18} /> Configured Sources</h3>
        {sources.length === 0 ? (
          <p className="text-sm text-gray-400">No sources have run yet. Run a discovery cycle to activate sources.</p>
        ) : (
          <div className="space-y-3">
            {sources.map(s => (
              <div key={s.id} className="flex items-center justify-between py-3 border-b last:border-b-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                    <Search size={18} className="text-blue-500" />
                  </div>
                  <div>
                    <p className="font-medium">{s.name}</p>
                    <p className="text-xs text-gray-500">{s.adapter_class}</p>
                  </div>
                </div>
                <div className="text-right text-sm">
                  <p className="text-gray-600">{s.jobs_found} jobs found</p>
                  {s.last_run && (
                    <p className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock size={12} /> Last: {new Date(s.last_run).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Sources */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold flex items-center gap-2 mb-4"><CheckCircle size={18} /> Available Adapters</h3>
        <div className="space-y-2">
          {available.map(a => (
            <div key={a.name} className="flex items-center gap-3 py-2">
              <span className="w-2 h-2 bg-green-400 rounded-full" />
              <span className="text-sm font-medium">{a.name}</span>
              <span className="text-xs text-gray-400">({a.class})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
