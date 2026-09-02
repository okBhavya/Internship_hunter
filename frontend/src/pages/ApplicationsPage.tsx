import { useEffect, useState } from 'react';
import { api, Application } from '../api';
import { FileText, Eye, CheckCircle, XCircle, Clock, ExternalLink, MessageSquare, Star } from 'lucide-react';

const STATUS_TABS = [
  { key: '', label: 'All', icon: FileText },
  { key: 'discovered', label: 'Discovered', icon: Eye },
  { key: 'shortlisted', label: 'Shortlisted', icon: Star },
  { key: 'prepared', label: 'Prepared', icon: FileText },
  { key: 'awaiting_approval', label: 'Awaiting', icon: Clock },
  { key: 'applied', label: 'Applied', icon: CheckCircle },
  { key: 'interview', label: 'Interview', icon: MessageSquare },
  { key: 'rejected', label: 'Rejected', icon: XCircle },
];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('');
  const [selectedApp, setSelectedApp] = useState<Application | null>(null);
  const [materials, setMaterials] = useState<any>(null);

  const fetchApps = () => {
    setLoading(true);
    api.getApplications(activeTab || undefined).then(setApplications).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(fetchApps, [activeTab]);

  const loadMaterials = async (appId: number) => {
    try {
      const data = await api.getApplication(appId);
      setSelectedApp(data);
      setMaterials(data.materials || null);
    } catch (e) { console.error(e); }
  };

  const handleApprove = async (appId: number) => {
    if (!confirm('Approve this application? This marks it as submitted.')) return;
    try {
      await api.approveApplication(appId);
      fetchApps();
      setSelectedApp(null);
    } catch (e: any) { alert('Error: ' + e.message); }
  };

  const handleSkip = async (appId: number) => {
    if (!confirm('Skip/withdraw this application?')) return;
    try {
      await api.skipApplication(appId);
      fetchApps();
      setSelectedApp(null);
    } catch (e: any) { alert('Error: ' + e.message); }
  };

  const statusColors: Record<string, string> = {
    discovered: 'bg-gray-100 text-gray-600',
    shortlisted: 'bg-blue-100 text-blue-600',
    prepared: 'bg-purple-100 text-purple-600',
    awaiting_approval: 'bg-yellow-100 text-yellow-700',
    applied: 'bg-green-100 text-green-700',
    interview: 'bg-indigo-100 text-indigo-700',
    rejected: 'bg-red-100 text-red-600',
    offer: 'bg-emerald-100 text-emerald-700',
    withdrawn: 'bg-gray-100 text-gray-500',
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Applications</h1>

      {/* Status Tabs */}
      <div className="flex gap-1 bg-white rounded-xl shadow-sm border p-1 overflow-x-auto">
        {STATUS_TABS.map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-colors ${
              activeTab === tab.key ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}>
            <tab.icon size={14} />
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
      ) : applications.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center text-gray-400">
          <FileText size={48} className="mx-auto mb-4 opacity-50" />
          <p className="text-lg">No applications found</p>
          <p className="text-sm mt-2">Go to Jobs or Top Matches to prepare applications</p>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map(app => (
            <div key={app.id} className="bg-white rounded-xl shadow-sm border p-4 hover:shadow-md transition-all cursor-pointer"
              onClick={() => loadMaterials(app.id)}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold">{app.job?.title || 'Unknown Job'}</h3>
                  <p className="text-sm text-gray-500">{app.job?.company || ''}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[app.status] || 'bg-gray-100 text-gray-500'}`}>
                      {app.status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </span>
                    {app.date_applied && (
                      <span className="text-xs text-gray-400">Applied {app.date_applied.split('T')[0]}</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  {app.job?.application_url && (
                    <a href={app.job.application_url} target="_blank" rel="noopener noreferrer"
                      onClick={e => e.stopPropagation()}
                      className="text-blue-500 hover:text-blue-700 text-sm flex items-center gap-1">
                      <ExternalLink size={14} /> Open
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Material Detail Modal */}
      {selectedApp && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => { setSelectedApp(null); setMaterials(null); }}>
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] overflow-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedApp.job?.title}</h2>
                <p className="text-gray-500">{selectedApp.job?.company}</p>
              </div>
              <button onClick={() => { setSelectedApp(null); setMaterials(null); }} className="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
            </div>

            {materials && (
              <div className="space-y-4">
                {materials.cover_letter && (
                  <div>
                    <h3 className="font-semibold text-sm text-gray-700 mb-1">Cover Letter</h3>
                    <pre className="text-sm bg-gray-50 p-4 rounded-lg whitespace-pre-wrap font-sans">{materials.cover_letter}</pre>
                  </div>
                )}
                {materials.summary && (
                  <div>
                    <h3 className="font-semibold text-sm text-gray-700 mb-1">Application Summary</h3>
                    <p className="text-sm bg-gray-50 p-4 rounded-lg">{materials.summary}</p>
                  </div>
                )}
                {materials.skills_summary && (
                  <div>
                    <h3 className="font-semibold text-sm text-gray-700 mb-1">Skills Summary</h3>
                    <p className="text-sm bg-gray-50 p-4 rounded-lg">{materials.skills_summary}</p>
                  </div>
                )}
                {materials.why_company && (
                  <div>
                    <h3 className="font-semibold text-sm text-gray-700 mb-1">Why This Company?</h3>
                    <p className="text-sm bg-gray-50 p-4 rounded-lg">{materials.why_company}</p>
                  </div>
                )}
                {materials.why_role && (
                  <div>
                    <h3 className="font-semibold text-sm text-gray-700 mb-1">Why This Role?</h3>
                    <p className="text-sm bg-gray-50 p-4 rounded-lg">{materials.why_role}</p>
                  </div>
                )}
                {materials.question_answers?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-sm text-gray-700 mb-1">Question Answers</h3>
                    <div className="space-y-2">
                      {materials.question_answers.map((qa: any, i: number) => (
                        <div key={i} className="bg-gray-50 p-3 rounded-lg">
                          <p className="text-sm font-medium text-gray-800">{qa.question}</p>
                          <p className="text-sm text-gray-600 mt-1">{qa.answer}</p>
                          {qa.needs_approval && <span className="text-xs text-yellow-600 mt-1 inline-block">⚠ Needs approval</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-3 mt-6">
              <button onClick={() => handleApprove(selectedApp.id)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 flex items-center gap-2">
                <CheckCircle size={14} /> Approve & Mark Submitted
              </button>
              <button onClick={() => handleSkip(selectedApp.id)}
                className="px-4 py-2 bg-red-100 text-red-600 rounded-lg text-sm hover:bg-red-200">
                Skip / Withdraw
              </button>
              {selectedApp.job?.application_url && (
                <a href={selectedApp.job.application_url} target="_blank" rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-2">
                  <ExternalLink size={14} /> Open Application Page
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
