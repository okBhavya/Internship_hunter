import { useEffect, useState } from 'react';
import { api } from '../api';
import { Settings, Plus, X, Save } from 'lucide-react';

export default function SearchSettingsPage() {
  const [prefs, setPrefs] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [newCountry, setNewCountry] = useState('');

  useEffect(() => {
    api.getSearchPreferences().then(setPrefs).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateSearchPreferences(prefs);
      alert('Settings saved!');
    } catch (e: any) { alert('Error: ' + e.message); }
    setSaving(false);
  };

  const addKeyword = () => {
    if (!newKeyword.trim()) return;
    setPrefs({ ...prefs, keywords: [...(prefs.keywords || []), newKeyword.trim()] });
    setNewKeyword('');
  };

  const removeKeyword = (i: number) => {
    setPrefs({ ...prefs, keywords: prefs.keywords.filter((_: string, idx: number) => idx !== i) });
  };

  const addCountry = () => {
    if (!newCountry.trim()) return;
    setPrefs({ ...prefs, preferred_countries: [...(prefs.preferred_countries || []), newCountry.trim()] });
    setNewCountry('');
  };

  const removeCountry = (i: number) => {
    setPrefs({ ...prefs, preferred_countries: prefs.preferred_countries.filter((_: string, idx: number) => idx !== i) });
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  if (!prefs) return <p className="text-gray-400">No preferences found.</p>;

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900">Search Settings</h1>

      {/* Keywords */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold flex items-center gap-2 mb-4"><Settings size={18} /> Search Keywords</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          {prefs.keywords?.map((kw: string, i: number) => (
            <span key={i} className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">
              {kw}
              <button onClick={() => removeKeyword(i)} className="hover:text-red-500"><X size={12} /></button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input value={newKeyword} onChange={e => setNewKeyword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addKeyword()}
            placeholder="Add keyword..." className="flex-1 border rounded-lg px-3 py-2 text-sm" />
          <button onClick={addKeyword} className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-1">
            <Plus size={14} /> Add
          </button>
        </div>
      </div>

      {/* Preferences */}
      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
        <h3 className="font-semibold">Filters</h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Fit Score</label>
            <input type="number" min="0" max="100" value={prefs.min_fit_score}
              onChange={e => setPrefs({ ...prefs, min_fit_score: parseInt(e.target.value) || 0 })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Results</label>
            <input type="number" min="10" max="500" value={prefs.max_results}
              onChange={e => setPrefs({ ...prefs, max_results: parseInt(e.target.value) || 100 })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <label className="flex items-center gap-3 text-sm">
          <input type="checkbox" checked={prefs.remote_only ?? true}
            onChange={e => setPrefs({ ...prefs, remote_only: e.target.checked })} className="rounded" />
          Remote positions only
        </label>

        <label className="flex items-center gap-3 text-sm">
          <input type="checkbox" checked={prefs.require_sponsorship_eligible}
            onChange={e => setPrefs({ ...prefs, require_sponsorship_eligible: e.target.checked })} className="rounded" />
          Only show jobs that may offer sponsorship
        </label>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Employment Types</label>
          <div className="flex flex-wrap gap-3">
            {['internship', 'co_op'].map(t => (
              <label key={t} className="flex items-center gap-1.5 text-sm">
                <input type="checkbox"
                  checked={prefs.employment_types?.includes(t)}
                  onChange={e => {
                    const types = prefs.employment_types || [];
                    setPrefs({
                      ...prefs,
                      employment_types: e.target.checked ? [...types, t] : types.filter((x: string) => x !== t),
                    });
                  }}
                  className="rounded" />
                {t.replace('_', ' ')}
              </label>
            ))}
          </div>
        </div>

        {/* Preferred Countries */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Countries</label>
          <div className="flex flex-wrap gap-2 mb-2">
            {prefs.preferred_countries?.map((c: string, i: number) => (
              <span key={i} className="inline-flex items-center gap-1 bg-green-50 text-green-700 px-3 py-1 rounded-full text-sm">
                {c}
                <button onClick={() => removeCountry(i)} className="hover:text-red-500"><X size={12} /></button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input value={newCountry} onChange={e => setNewCountry(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addCountry()}
              placeholder="Add country..." className="flex-1 border rounded-lg px-3 py-2 text-sm" />
            <button onClick={addCountry} className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
              <Plus size={14} />
            </button>
          </div>
        </div>
      </div>

      <button onClick={handleSave} disabled={saving}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 font-medium">
        <Save size={16} /> {saving ? 'Saving...' : 'Save Settings'}
      </button>
    </div>
  );
}
