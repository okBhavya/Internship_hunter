import { useEffect, useState } from 'react';
import { api } from '../api';
import type { User } from '../api';
import { User as UserIcon, GraduationCap, Code, Briefcase, Award, Upload, Plus, X } from 'lucide-react';

export default function ProfilesPage() {
  const [profile, setProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [newSkill, setNewSkill] = useState({ name: '', category: 'programming', proficiency: 'intermediate' });
  const [showAddEducation, setShowAddEducation] = useState(false);
  const [newEdu, setNewEdu] = useState({ university: '', degree: '', field_of_study: '', location: '', start_date: '', end_date: '', gpa: '' });
  const [showAddProject, setShowAddProject] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '', technologies: '', url: '' });
  const [showAddExperience, setShowAddExperience] = useState(false);
  const [newExp, setNewExperience] = useState({ company: '', title: '', location: '', start_date: '', end_date: '', description: '' });

  const fetchProfile = () => {
    api.getProfile().then(setProfile).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(fetchProfile, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await api.uploadResume(file);
      fetchProfile();
    } catch (e: any) { alert('Upload failed: ' + e.message); }
    setUploading(false);
  };

  const handleAddSkill = async () => {
    if (!newSkill.name) return;
    await api.addSkill(newSkill);
    setNewSkill({ name: '', category: 'programming', proficiency: 'intermediate' });
    setShowAddSkill(false);
    fetchProfile();
  };

  const handleAddEducation = async () => {
    if (!newEdu.university || !newEdu.degree) return;
    await api.addEducation(newEdu);
    setNewEdu({ university: '', degree: '', field_of_study: '', location: '', start_date: '', end_date: '', gpa: '' });
    setShowAddEducation(false);
    fetchProfile();
  };

  const handleAddProject = async () => {
    if (!newProject.name) return;
    await api.addProject(newProject);
    setNewProject({ name: '', description: '', technologies: '', url: '' });
    setShowAddProject(false);
    fetchProfile();
  };

  const handleAddExperience = async () => {
    if (!newExp.company || !newExp.title) return;
    await api.addExperience(newExp);
    setNewExperience({ company: '', title: '', location: '', start_date: '', end_date: '', description: '' });
    setShowAddExperience(false);
    fetchProfile();
  };

  const handleDelete = async (type: string, id: number) => {
    if (!confirm('Delete this item?')) return;
    if (type === 'skill') await api.deleteSkill(id);
    else if (type === 'education') await api.deleteEducation(id);
    else if (type === 'project') await api.deleteProject(id);
    else if (type === 'experience') await api.deleteExperience(id);
    fetchProfile();
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Resume & Profile</h1>

      {/* Resume Upload */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold flex items-center gap-2 mb-4"><Upload size={18} /> Resumes</h3>
        <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center">
          <input type="file" accept=".pdf" onChange={handleUpload} className="hidden" id="resume-upload" />
          <label htmlFor="resume-upload" className="cursor-pointer text-blue-600 hover:text-blue-700">
            {uploading ? 'Uploading...' : '📄 Click to upload resume (PDF)'}
          </label>
        </div>
        {profile?.resumes?.length ? (
          <div className="mt-3 space-y-2">
            {profile.resumes.map(r => (
              <div key={r.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                <span className="text-sm">{r.filename}</span>
                {r.is_primary && <span className="text-xs bg-green-100 text-green-600 px-2 py-0.5 rounded-full">Primary</span>}
              </div>
            ))}
          </div>
        ) : null}
      </div>

      {/* Basic Info */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold flex items-center gap-2 mb-4"><UserIcon size={18} /> Basic Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Name:</span> <span className="font-medium">{profile?.name}</span></div>
          <div><span className="text-gray-500">Email:</span> <span className="font-medium">{profile?.email}</span></div>
          <div><span className="text-gray-500">Phone:</span> <span className="font-medium">{profile?.phone}</span></div>
          <div><span className="text-gray-500">Location:</span> <span className="font-medium">{profile?.location}</span></div>
          <div><span className="text-gray-500">Citizenship:</span> <span className="font-medium">{profile?.citizenship}</span></div>
          <div><span className="text-gray-500">Sponsorship:</span> <span className="font-medium">{profile?.requires_sponsorship ? 'Required' : 'Not Required'}</span></div>
          <div><span className="text-gray-500">LinkedIn:</span> <a href={profile?.linkedin_url} className="text-blue-600 hover:underline" target="_blank">{profile?.linkedin_url}</a></div>
          <div><span className="text-gray-500">GitHub:</span> <a href={profile?.github_url} className="text-blue-600 hover:underline" target="_blank">{profile?.github_url}</a></div>
        </div>
      </div>

      {/* Education */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold flex items-center gap-2"><GraduationCap size={18} /> Education</h3>
          <button onClick={() => setShowAddEducation(!showAddEducation)} className="text-blue-600 text-sm flex items-center gap-1 hover:text-blue-700">
            <Plus size={14} /> Add
          </button>
        </div>
        {showAddEducation && (
          <div className="bg-blue-50 p-4 rounded-lg mb-3 grid grid-cols-2 gap-3">
            <input placeholder="University" value={newEdu.university} onChange={e => setNewEdu({...newEdu, university: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <input placeholder="Degree" value={newEdu.degree} onChange={e => setNewEdu({...newEdu, degree: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <input placeholder="Field of Study" value={newEdu.field_of_study} onChange={e => setNewEdu({...newEdu, field_of_study: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <input placeholder="Start - End Date" value={newEdu.start_date} onChange={e => setNewEdu({...newEdu, start_date: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <button onClick={handleAddEducation} className="bg-blue-600 text-white rounded px-4 py-1.5 text-sm hover:bg-blue-700">Save</button>
            <button onClick={() => setShowAddEducation(false)} className="text-gray-500 text-sm">Cancel</button>
          </div>
        )}
        {profile?.education_entries?.map(edu => (
          <div key={edu.id} className="flex items-center justify-between py-2 border-b last:border-b-0">
            <div>
              <p className="font-medium">{edu.degree} {edu.field_of_study && `in ${edu.field_of_study}`}</p>
              <p className="text-sm text-gray-500">{edu.university} • {edu.start_date} - {edu.end_date}</p>
            </div>
            <button onClick={() => handleDelete('education', edu.id)} className="text-red-400 hover:text-red-600"><X size={16} /></button>
          </div>
        ))}
      </div>

      {/* Skills */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold flex items-center gap-2"><Code size={18} /> Skills</h3>
          <button onClick={() => setShowAddSkill(!showAddSkill)} className="text-blue-600 text-sm flex items-center gap-1 hover:text-blue-700">
            <Plus size={14} /> Add
          </button>
        </div>
        {showAddSkill && (
          <div className="bg-blue-50 p-4 rounded-lg mb-3 flex gap-3 items-end">
            <input placeholder="Skill name" value={newSkill.name} onChange={e => setNewSkill({...newSkill, name: e.target.value})} className="border rounded px-3 py-1.5 text-sm flex-1" />
            <select value={newSkill.category} onChange={e => setNewSkill({...newSkill, category: e.target.value})} className="border rounded px-3 py-1.5 text-sm">
              <option value="programming">Programming</option>
              <option value="framework">Framework</option>
              <option value="ml">ML/AI</option>
              <option value="cloud">Cloud</option>
              <option value="tool">Tool</option>
            </select>
            <button onClick={handleAddSkill} className="bg-blue-600 text-white rounded px-4 py-1.5 text-sm hover:bg-blue-700">Save</button>
          </div>
        )}
        <div className="flex flex-wrap gap-2">
          {profile?.skills?.map(skill => (
            <span key={skill.id} className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">
              {skill.name}
              <button onClick={() => handleDelete('skill', skill.id)} className="hover:text-red-500"><X size={12} /></button>
            </span>
          ))}
        </div>
      </div>

      {/* Experience */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold flex items-center gap-2"><Briefcase size={18} /> Experience</h3>
          <button onClick={() => setShowAddExperience(!showAddExperience)} className="text-blue-600 text-sm flex items-center gap-1 hover:text-blue-700">
            <Plus size={14} /> Add
          </button>
        </div>
        {showAddExperience && (
          <div className="bg-blue-50 p-4 rounded-lg mb-3 grid grid-cols-2 gap-3">
            <input placeholder="Company" value={newExp.company} onChange={e => setNewExperience({...newExp, company: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <input placeholder="Title" value={newExp.title} onChange={e => setNewExperience({...newExp, title: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <input placeholder="Location" value={newExp.location} onChange={e => setNewExperience({...newExp, location: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <input placeholder="Start - End" value={newExp.start_date} onChange={e => setNewExperience({...newExp, start_date: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <textarea placeholder="Description" value={newExp.description} onChange={e => setNewExperience({...newExp, description: e.target.value})} className="border rounded px-3 py-1.5 text-sm col-span-2" rows={2} />
            <button onClick={handleAddExperience} className="bg-blue-600 text-white rounded px-4 py-1.5 text-sm hover:bg-blue-700">Save</button>
          </div>
        )}
        {profile?.experiences?.map(exp => (
          <div key={exp.id} className="flex items-start justify-between py-3 border-b last:border-b-0">
            <div>
              <p className="font-medium">{exp.title}</p>
              <p className="text-sm text-gray-500">{exp.company} • {exp.location}</p>
              <p className="text-sm text-gray-500">{exp.start_date} - {exp.end_date}</p>
              <p className="text-sm text-gray-600 mt-1">{exp.description}</p>
            </div>
            <button onClick={() => handleDelete('experience', exp.id)} className="text-red-400 hover:text-red-600"><X size={16} /></button>
          </div>
        ))}
      </div>

      {/* Projects */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold flex items-center gap-2"><Award size={18} /> Projects</h3>
          <button onClick={() => setShowAddProject(!showAddProject)} className="text-blue-600 text-sm flex items-center gap-1 hover:text-blue-700">
            <Plus size={14} /> Add
          </button>
        </div>
        {showAddProject && (
          <div className="bg-blue-50 p-4 rounded-lg mb-3 grid grid-cols-2 gap-3">
            <input placeholder="Project name" value={newProject.name} onChange={e => setNewProject({...newProject, name: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <input placeholder="Technologies" value={newProject.technologies} onChange={e => setNewProject({...newProject, technologies: e.target.value})} className="border rounded px-3 py-1.5 text-sm" />
            <textarea placeholder="Description" value={newProject.description} onChange={e => setNewProject({...newProject, description: e.target.value})} className="border rounded px-3 py-1.5 text-sm col-span-2" rows={2} />
            <button onClick={handleAddProject} className="bg-blue-600 text-white rounded px-4 py-1.5 text-sm hover:bg-blue-700">Save</button>
          </div>
        )}
        {profile?.projects?.map(proj => (
          <div key={proj.id} className="flex items-start justify-between py-3 border-b last:border-b-0">
            <div>
              <p className="font-medium">{proj.name}</p>
              <p className="text-sm text-gray-500">Tech: {proj.technologies}</p>
              <p className="text-sm text-gray-600 mt-1">{proj.description}</p>
            </div>
            <button onClick={() => handleDelete('project', proj.id)} className="text-red-400 hover:text-red-600"><X size={16} /></button>
          </div>
        ))}
      </div>
    </div>
  );
}
