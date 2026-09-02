import { useEffect, useState } from 'react';
import { api, AgentRun } from '../api';
import { Activity, CheckCircle, XCircle, Clock, AlertTriangle, Loader } from 'lucide-react';

export default function AgentActivityPage() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAgentRuns(50).then(setRuns).catch(console.error).finally(() => setLoading(false));
  }, []);

  const statusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle size={16} className="text-green-500" />;
      case 'failed': return <XCircle size={16} className="text-red-500" />;
      case 'running': return <Loader size={16} className="text-blue-500 animate-spin" />;
      case 'waiting': return <Clock size={16} className="text-yellow-500" />;
      case 'blocked': return <AlertTriangle size={16} className="text-orange-500" />;
      default: return <Activity size={16} className="text-gray-400" />;
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-50 text-green-700 border-green-200';
      case 'failed': return 'bg-red-50 text-red-700 border-red-200';
      case 'running': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'waiting': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'blocked': return 'bg-orange-50 text-orange-700 border-orange-200';
      default: return 'bg-gray-50 text-gray-500 border-gray-200';
    }
  };

  const agentColors: Record<string, string> = {
    job_discovery: 'bg-blue-100 text-blue-700',
    job_matching: 'bg-purple-100 text-purple-700',
    resume_tailoring: 'bg-green-100 text-green-700',
    cover_letter: 'bg-pink-100 text-pink-700',
    application_question: 'bg-indigo-100 text-indigo-700',
    duplicate_detection: 'bg-orange-100 text-orange-700',
    verification: 'bg-teal-100 text-teal-700',
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Agent Activity</h1>
      <p className="text-sm text-gray-500">Monitor all agent runs, decisions, and outputs.</p>

      {runs.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center text-gray-400">
          <Activity size={48} className="mx-auto mb-4 opacity-50" />
          <p className="text-lg">No agent activity yet</p>
          <p className="text-sm mt-2">Run a discovery cycle to see agent activity here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {runs.map(run => (
            <div key={run.id} className={`bg-white rounded-xl shadow-sm border p-4 ${statusColor(run.status)}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {statusIcon(run.status)}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${agentColors[run.agent_name] || 'bg-gray-100 text-gray-600'}`}>
                        {run.agent_name}
                      </span>
                      <span className="text-sm font-medium capitalize">{run.status}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{run.task}</p>
                  </div>
                </div>
                <div className="text-right text-xs text-gray-400">
                  <div>{new Date(run.started_at).toLocaleString()}</div>
                  {run.duration_seconds != null && <div>{Math.round(run.duration_seconds)}s</div>}
                </div>
              </div>

              {run.actions?.length > 0 && (
                <div className="mt-3 pl-6 space-y-1">
                  {run.actions.map((a: any, i: number) => (
                    <div key={i} className="text-xs text-gray-500 flex items-start gap-1">
                      <span className="text-gray-300">→</span>
                      {typeof a === 'string' ? a : a.action || JSON.stringify(a)}
                    </div>
                  ))}
                </div>
              )}

              {run.errors?.length > 0 && (
                <div className="mt-2 pl-6 space-y-1">
                  {run.errors.map((e: any, i: number) => (
                    <div key={i} className="text-xs text-red-500">
                      ✗ {typeof e === 'string' ? e : e.error || JSON.stringify(e)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
