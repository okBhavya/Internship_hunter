import { useState } from 'react';
import { api } from '../api';
import { CheckCircle, Upload, Settings, Search, Rocket, Loader } from 'lucide-react';

const STEPS = [
  { id: 1, label: 'Seed Profile', icon: CheckCircle, description: 'Load your resume data into the system' },
  { id: 2, label: 'Configure Search', icon: Settings, description: 'Set up job search keywords and filters' },
  { id: 3, label: 'Run Discovery', icon: Search, description: 'Find your first batch of opportunities' },
  { id: 4, label: 'View Results', icon: Rocket, description: 'See top matches ranked by fit score' },
];

export default function SetupPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [error, setError] = useState('');

  const runStep = async (step: number) => {
    setLoading(true);
    setError('');
    try {
      if (step === 1) {
        await api.seedProfile();
      } else if (step === 2) {
        await api.seedPreferences();
      } else if (step === 3) {
        await api.orchestrateDiscovery();
      }
      setCompletedSteps([...completedSteps, step]);
      setCurrentStep(step + 1);
    } catch (e: any) {
      setError(e.message || 'Something went wrong');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">🎯 Welcome to Internship Hunter</h1>
        <p className="text-gray-500 mt-2">Let's get you set up in a few simple steps.</p>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        {STEPS.map((step) => {
          const isCompleted = completedSteps.includes(step.id);
          const isCurrent = currentStep === step.id;
          const isLocked = step.id > currentStep;

          return (
            <div key={step.id}
              className={`bg-white rounded-xl shadow-sm border p-5 transition-all ${
                isCurrent ? 'ring-2 ring-blue-500 shadow-md' : isLocked ? 'opacity-50' : ''
              }`}>
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                  isCompleted ? 'bg-green-500' : isCurrent ? 'bg-blue-500' : 'bg-gray-300'
                }`}>
                  {isCompleted ? '✓' : step.id}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">{step.label}</h3>
                  <p className="text-sm text-gray-500">{step.description}</p>
                </div>
                {isCurrent && !isCompleted && (
                  <button onClick={() => runStep(step.id)} disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 text-sm font-medium">
                    {loading ? <Loader size={14} className="animate-spin" /> : null}
                    {loading ? 'Running...' : 'Run Step'}
                  </button>
                )}
                {isCompleted && (
                  <CheckCircle size={20} className="text-green-500" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">
          {error}
        </div>
      )}

      {completedSteps.length === STEPS.length && (
        <div className="text-center bg-green-50 rounded-xl p-8 border border-green-200">
          <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
          <h2 className="text-xl font-bold text-green-800">Setup Complete!</h2>
          <p className="text-green-600 mt-2">Your profile is loaded and jobs have been discovered.</p>
          <div className="flex gap-3 justify-center mt-4">
            <a href="/matches" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
              View Top Matches
            </a>
            <a href="/jobs" className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium">
              Browse All Jobs
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
