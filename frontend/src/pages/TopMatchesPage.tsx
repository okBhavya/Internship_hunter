import { useEffect, useState } from 'react';
import { api } from '../api';
import type { Job, JobMatch } from '../api';
import { Star, ExternalLink, MapPin, Building2, AlertTriangle, CheckCircle } from 'lucide-react';

export default function TopMatchesPage() {
  const [matches, setMatches] = useState<{ job: Job; match: JobMatch }[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<{ job: Job; match: JobMatch } | null>(null);

  useEffect(() => {
    api.getTopMatches(30).then(setMatches).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handlePrepare = async (jobId: number) => {
    try {
      await api.createApplication(jobId, 'prepare');
      alert('Application materials prepared! Check the Applications tab.');
    } catch (e: any) { alert('Error: ' + e.message); }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'from-green-500 to-emerald-500';
    if (score >= 55) return 'from-yellow-500 to-orange-500';
    return 'from-red-400 to-pink-500';
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Top Matches</h1>
      <p className="text-gray-500">Jobs ranked by AI fit score against your profile.</p>

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
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">{job.title}</h3>
                  <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                    <Building2 size={14} />{job.company}
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-sm text-gray-400">
                    <MapPin size={14} />{job.location || 'Remote'}
                  </div>
                </div>
                <div className={`bg-gradient-to-br ${getScoreColor(match.fit_score)} text-white px-3 py-2 rounded-xl text-center`}>
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
                <div className="text-xs text-green-600 mb-1">✓ {match.strengths[0]}</div>
              )}
              {match.concerns?.length > 0 && (
                <div className="text-xs text-orange-500">⚠ {match.concerns[0]}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
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

            <div className="flex gap-3 mt-4">
              {selectedJob.job.application_url && (
                <a href={selectedJob.job.application_url} target="_blank" rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-2">
                  <ExternalLink size={14} /> Apply
                </a>
              )}
              <button onClick={() => { handlePrepare(selectedJob.job.id); setSelectedJob(null); }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                📝 Prepare Application
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
