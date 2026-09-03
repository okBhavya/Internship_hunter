import { useEffect, useState, useCallback } from 'react';
import { api, type Job, type JobMatch, type AutoApplyResult } from '../api';
import { Star, ExternalLink, MapPin, Building2, AlertTriangle, CheckCircle, Bot, Loader2, X, ShieldAlert } from 'lucide-react';

interface AutoApplyStatus {
  [jobId: number]: {
    status: 'loading' | 'filled' | 'blocked' | 'error';
    message: string;
  };
}

export default function TopMatchesPage() {
  const [matches, setMatches] = useState<{ job: Job; match: JobMatch }[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<{ job: Job; match: JobMatch } | null>(null);
  const [autoApplyStatus, setAutoApplyStatus] = useState<AutoApplyStatus>({});

  useEffect(() => {
    api.getTopMatches(30).then(setMatches).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handlePrepare = async (jobId: number) => {
    try {
      await api.createApplication(jobId, 'prepare');
      alert('Application materials prepared! Check the Applications tab.');
    } catch (e: any) { alert('Error: ' + e.message); }
  };

  const handleAutoApply = useCallback(async (job: Job, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const jobId = job.id;
    setAutoApplyStatus(prev => ({ ...prev, [jobId]: { status: 'loading', message: 'Detecting application form...' } }));
    try {
      const result = await api.autoFillApplications([jobId], false);
      const r = result.results?.[0];
      if (!r) {
        setAutoApplyStatus(prev => ({ ...prev, [jobId]: { status: 'error', message: 'No result returned' } }));
        return;
      }
      if (r.status === 'filled') {
        setAutoApplyStatus(prev => ({ ...prev, [jobId]: {
          status: 'filled',
          message: `Filled ${r.fields_filled}/${r.fields_total} fields${r.resume_uploaded ? ', resume uploaded' : ''}${r.cover_letter_filled ? ', cover letter added' : ''}`,
        }}));
      } else if (r.status === 'blocked') {
        setAutoApplyStatus(prev => ({ ...prev, [jobId]: {
          status: 'blocked',
          message: r.blocked_by ? `Blocked by ${r.blocked_by}` : 'No application form found on this page',
        }}));
      } else {
        setAutoApplyStatus(prev => ({ ...prev, [jobId]: {
          status: 'error',
          message: r.error || 'Unknown error',
        }}));
      }
    } catch (err: any) {
      setAutoApplyStatus(prev => ({ ...prev, [jobId]: { status: 'error', message: err.message || 'Auto-apply failed' } }));
    }
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'from-green-500 to-emerald-500';
    if (score >= 55) return 'from-yellow-500 to-orange-500';
    return 'from-red-400 to-pink-500';
  };

  const AutoApplyButton = ({ job, className = '' }: { job: Job; className?: string }) => {
    const status = autoApplyStatus[job.id];
    if (status?.status === 'loading') {
      return (
        <button disabled className={`px-3 py-1.5 bg-indigo-400 text-white rounded-lg text-xs font-medium flex items-center gap-1 ${className}`}>
          <Loader2 size={12} className="animate-spin" /> Applying...
        </button>
      );
    }
    if (status?.status === 'filled') {
      return (
        <span className={`px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-xs font-medium flex items-center gap-1 ${className}`}>
          <CheckCircle size={12} /> Filled
        </span>
      );
    }
    if (status?.status === 'blocked') {
      return (
        <span className={`px-3 py-1.5 bg-orange-100 text-orange-700 rounded-lg text-xs font-medium flex items-center gap-1 ${className}`} title={status.message}>
          <ShieldAlert size={12} /> Blocked
        </span>
      );
    }
    if (status?.status === 'error') {
      return (
        <span className={`px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-xs font-medium flex items-center gap-1 ${className}`} title={status.message}>
          <X size={12} /> Failed
        </span>
      );
    }
    return (
      <button onClick={(e) => handleAutoApply(job, e)}
        className={`px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 transition-colors flex items-center gap-1 ${className}`}>
        <Bot size={12} /> Auto-Apply
      </button>
    );
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Top Matches</h1>
        <p className="text-gray-500">Jobs ranked by AI fit score. Prepare or auto-apply directly.</p>
      </div>

      {matches.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center text-gray-400">
          <Star size={48} className="mx-auto mb-4 opacity-50" />
          <p className="text-lg">No matches yet</p>
          <p className="text-sm mt-2">Run a discovery cycle to find and score jobs</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {matches.map(({ job, match }) => (
            <div key={job.id} onClick={() => setSelectedJob({ job, match })}
              className="bg-white rounded-xl shadow-sm border p-5 cursor-pointer hover:shadow-md transition-all group">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">{job.title}</h3>
                  <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                    <Building2 size={14} />{job.company}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-sm text-gray-400">
                    <MapPin size={14} />{job.location || 'Remote'}
                  </div>
                </div>
                <div className={`bg-gradient-to-br ${getScoreColor(match.fit_score)} text-white px-3 py-2 rounded-xl text-center shrink-0`}>
                  <div className="text-2xl font-bold">{match.fit_score}</div>
                  <div className="text-xs opacity-80">/100</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-1 mb-3">
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  match.recommendation === 'APPLY' ? 'bg-green-100 text-green-700' :
                  match.recommendation === 'CONSIDER' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-500'
                }`}>
                  {match.recommendation === 'APPLY' && <CheckCircle size={12} className="inline mr-1" />}
                  {match.recommendation === 'SKIP' && <AlertTriangle size={12} className="inline mr-1" />}
                  {match.recommendation}
                </span>
                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{job.remote_type}</span>
                <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded-full">{job.internship_or_fulltime}</span>
              </div>

              {match.strengths?.length > 0 && (
                <div className="text-xs text-green-600 mb-1">{`\u2713`} {match.strengths[0]}</div>
              )}
              {match.concerns?.length > 0 && (
                <div className="text-xs text-orange-500">{`\u26a0`} {match.concerns[0]}</div>
              )}

              {autoApplyStatus[job.id] && autoApplyStatus[job.id].status !== 'loading' && (
                <div className={`text-xs mt-2 px-2 py-1 rounded ${
                  autoApplyStatus[job.id].status === 'filled' ? 'bg-green-50 text-green-700' :
                  autoApplyStatus[job.id].status === 'blocked' ? 'bg-orange-50 text-orange-700' :
                  'bg-red-50 text-red-600'
                }`}>
                  {autoApplyStatus[job.id].message}
                </div>
              )}

              <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100">
                <button onClick={(e) => { e.stopPropagation(); handlePrepare(job.id); }}
                  className="flex-1 px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 transition-colors">
                  Prepare
                </button>
                <AutoApplyButton job={job} />
                {job.application_url && (
                  <a href={job.application_url} target="_blank" rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg text-xs font-medium hover:bg-blue-100 transition-colors flex items-center gap-1">
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedJob && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setSelectedJob(null)}>
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedJob.job.title}</h2>
                <p className="text-gray-500">{selectedJob.job.company}</p>
              </div>
              <div className="text-center">
                <div className={`bg-gradient-to-br ${getScoreColor(selectedJob.match.fit_score)} text-white px-4 py-3 rounded-xl`}>
                  <div className="text-3xl font-bold">{selectedJob.match.fit_score}</div>
                </div>
                <span className="text-xs font-medium mt-1 block">{selectedJob.match.recommendation}</span>
              </div>
            </div>

            <p className="text-sm text-gray-600 mb-4">{selectedJob.match.explanation}</p>

            {selectedJob.match.missing_skills?.length > 0 && (
              <div className="bg-red-50 p-3 rounded-lg mb-3">
                <h4 className="text-xs font-semibold text-red-700 mb-1">Missing Skills</h4>
                <div className="flex flex-wrap gap-1">
                  {selectedJob.match.missing_skills.map(s => (
                    <span key={s} className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {autoApplyStatus[selectedJob.job.id] && autoApplyStatus[selectedJob.job.id].status !== 'loading' && (
              <div className={`p-3 rounded-lg mb-3 ${
                autoApplyStatus[selectedJob.job.id].status === 'filled' ? 'bg-green-50 border border-green-200' :
                autoApplyStatus[selectedJob.job.id].status === 'blocked' ? 'bg-orange-50 border border-orange-200' :
                'bg-red-50 border border-red-200'
              }`}>
                <p className={`text-sm font-medium ${
                  autoApplyStatus[selectedJob.job.id].status === 'filled' ? 'text-green-700' :
                  autoApplyStatus[selectedJob.job.id].status === 'blocked' ? 'text-orange-700' :
                  'text-red-700'
                }`}>
                  {autoApplyStatus[selectedJob.job.id].message}
                </p>
              </div>
            )}

            <div className="flex gap-3 mt-4 flex-wrap">
              <button onClick={() => handleAutoApply(selectedJob.job)}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 flex items-center gap-2">
                <Bot size={14} /> Auto-Apply
              </button>
              {selectedJob.job.application_url && (
                <a href={selectedJob.job.application_url} target="_blank" rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-2">
                  <ExternalLink size={14} /> Apply
                </a>
              )}
              <button onClick={() => { handlePrepare(selectedJob.job.id); setSelectedJob(null); }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                Prepare Application
              </button>
              <button onClick={() => setSelectedJob(null)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
