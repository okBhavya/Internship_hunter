import { useEffect, useState } from 'react';
import { api, type Job, type JobMatch } from '../api';
import { Search, Filter, ExternalLink, MapPin, Clock, Building2, ChevronDown } from 'lucide-react';

interface JobWithMatch { job: Job; match: JobMatch | null; }

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobWithMatch[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [internOnly, setInternOnly] = useState(false);
  const [sortBy, setSortBy] = useState('discovered_at');
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<JobWithMatch | null>(null);
  const [discovering, setDiscovering] = useState(false);

  const fetchJobs = () => {
    setLoading(true);
    const params: Record<string, string> = { page: String(page), limit: '20', sort_by: sortBy };
    if (search) params.search = search;
    if (remoteOnly) params.remote_only = 'true';
    if (internOnly) params.internship_only = 'true';

    api.getJobs(params).then(data => {
      setJobs(data.jobs);
      setTotal(data.total);
    }).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(fetchJobs, [page, sortBy, remoteOnly, internOnly]);

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); setPage(1); fetchJobs(); };

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      await api.orchestrateDiscovery();
      fetchJobs();
    } catch (e) { console.error(e); }
    setDiscovering(false);
  };

  const handlePrepare = async (jobId: number) => {
    try {
      await api.createApplication(jobId, 'prepare');
      alert('Application materials prepared!');
    } catch (e: any) { alert('Error: ' + e.message); }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-green-600 bg-green-50';
    if (score >= 55) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getRecommendationBadge = (rec: string) => {
    if (rec === 'APPLY') return 'bg-green-100 text-green-700';
    if (rec === 'CONSIDER') return 'bg-yellow-100 text-yellow-700';
    return 'bg-gray-100 text-gray-500';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Job Discovery</h1>
        <button onClick={handleDiscover} disabled={discovering}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium flex items-center gap-2">
          {discovering ? <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" /> : <Search size={16} />}
          {discovering ? 'Discovering...' : 'Run Discovery'}
        </button>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-xl shadow-sm border p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-center">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search jobs, companies..."
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          </div>
          <select value={sortBy} onChange={e => setSortBy(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm">
            <option value="discovered_at">Newest</option>
            <option value="fit_score">Best Match</option>
            <option value="title">Title A-Z</option>
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={remoteOnly} onChange={e => setRemoteOnly(e.target.checked)} className="rounded" />
            Remote Only
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={internOnly} onChange={e => setInternOnly(e.target.checked)} className="rounded" />
            Internships
          </label>
          <button type="submit" className="px-4 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200">Search</button>
        </form>
      </div>

      <div className="text-sm text-gray-500">{total} jobs found</div>

      {/* Job List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className={`${selectedJob ? 'lg:col-span-1' : 'lg:col-span-3'} space-y-3`}>
          {loading ? (
            <div className="flex items-center justify-center h-40"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
          ) : jobs.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border p-12 text-center text-gray-400">
              <Search size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg">No jobs found</p>
              <p className="text-sm mt-2">Try running a discovery cycle or adjusting your filters</p>
            </div>
          ) : (
            jobs.map(({ job, match }) => (
              <div key={job.id} onClick={() => setSelectedJob({ job, match })}
                className={`bg-white rounded-xl shadow-sm border p-4 cursor-pointer hover:shadow-md transition-all ${
                  selectedJob?.job.id === job.id ? 'ring-2 ring-blue-500' : ''}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{job.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><Building2 size={14} />{job.company}</span>
                      <span className="flex items-center gap-1"><MapPin size={14} />{job.location || 'Remote'}</span>
                      <span className="flex items-center gap-1"><Clock size={14} />{job.discovered_at?.split('T')[0]}</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {job.remote_type && <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{job.remote_type}</span>}
                      <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded-full">{job.internship_or_fulltime}</span>
                      {job.source_name && <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{job.source_name}</span>}
                    </div>
                  </div>
                  {match && (
                    <div className="text-right ml-4">
                      <div className={`text-2xl font-bold px-3 py-1 rounded-lg ${getScoreColor(match.fit_score)}`}>
                        {match.fit_score}
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${getRecommendationBadge(match.recommendation)}`}>
                        {match.recommendation}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detail Panel */}
        {selectedJob && (
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border p-6 sticky top-20 self-start max-h-[calc(100vh-120px)] overflow-auto">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedJob.job.title}</h2>
                <p className="text-gray-500">{selectedJob.job.company} • {selectedJob.job.location}</p>
              </div>
              <button onClick={() => setSelectedJob(null)} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
            </div>

            {selectedJob.match && (
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-sm mb-2">Fit Score Breakdown</h4>
                <div className="grid grid-cols-4 gap-2 text-xs">
                  {[
                    ['Technical', selectedJob.match.technical_match, 30],
                    ['Role', selectedJob.match.role_match, 20],
                    ['Experience', selectedJob.match.experience_match, 15],
                    ['Education', selectedJob.match.education_match, 10],
                    ['Location', selectedJob.match.location_match, 10],
                    ['Auth', selectedJob.match.authorization_match, 5],
                    ['Projects', selectedJob.match.project_match, 5],
                    ['Feasibility', selectedJob.match.feasibility_match, 5],
                  ].map(([label, score, max]) => (
                    <div key={String(label)} className="text-center">
                      <div className="font-bold text-sm">{score}/{max}</div>
                      <div className="text-gray-400">{label}</div>
                    </div>
                  ))}
                </div>
                {selectedJob.match.missing_skills?.length > 0 && (
                  <div className="mt-3">
                    <span className="text-xs font-medium text-red-500">Missing: </span>
                    <span className="text-xs text-gray-600">{selectedJob.match.missing_skills.join(', ')}</span>
                  </div>
                )}
                {selectedJob.match.strengths?.length > 0 && (
                  <div className="mt-1">
                    <span className="text-xs font-medium text-green-500">Strengths: </span>
                    <span className="text-xs text-gray-600">{selectedJob.match.strengths.join(', ')}</span>
                  </div>
                )}
              </div>
            )}

            <div className="prose prose-sm max-w-none mb-4 text-sm text-gray-700"
              dangerouslySetInnerHTML={{ __html: selectedJob.job.description?.replace(/\n/g, '<br/>').substring(0, 3000) || 'No description available' }} />

            <div className="flex gap-3">
              {selectedJob.job.application_url && (
                <a href={selectedJob.job.application_url} target="_blank" rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-2">
                  <ExternalLink size={14} /> Apply Now
                </a>
              )}
              <button onClick={() => handlePrepare(selectedJob.job.id)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">
                📝 Prepare Application
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50">Prev</button>
          <span className="text-sm text-gray-500">Page {page} of {Math.ceil(total / 20)}</span>
          <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 20)}
            className="px-3 py-1 border rounded text-sm disabled:opacity-50">Next</button>
        </div>
      )}
    </div>
  );
}
