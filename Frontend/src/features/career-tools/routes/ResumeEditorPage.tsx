import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Loader2, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { resumeApi, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { toast } from "sonner";

interface FormState {
  title: string;
  template_name: string;
  personal_info: {
    name: string;
    email: string;
    phone: string;
    location: string;
    linkedin: string;
    github: string;
    portfolio: string;
    summary: string;
  };
  skills: { items: string[] };
  skillInput: string;
  education: { items: any[] };
  work_experience: { items: any[] };
  projects: { items: any[] };
  certifications: { items: any[] };
}

const initialState: FormState = {
  title: "",
  template_name: "modern",
  personal_info: { name: "", email: "", phone: "", location: "", linkedin: "", github: "", portfolio: "", summary: "" },
  skills: { items: [] },
  skillInput: "",
  education: { items: [] },
  work_experience: { items: [] },
  projects: { items: [] },
  certifications: { items: [] },
};

export default function ResumeEditorPage() {
  const navigate = useNavigate();
  const { resumeId } = useParams();
  const isEditing = !!resumeId;

  const [form, setForm] = useState<FormState>(initialState);
  const [saving, setSaving] = useState(false);

  const updatePersonal = (field: string, value: string) => {
    setForm((prev) => ({
      ...prev,
      personal_info: { ...prev.personal_info, [field]: value },
    }));
  };

  const addSkill = () => {
    const skill = form.skillInput.trim();
    if (skill && !form.skills.items.includes(skill)) {
      setForm((prev) => ({
        ...prev,
        skills: { items: [...prev.skills.items, skill] },
        skillInput: "",
      }));
    }
  };

  const removeSkill = (skill: string) => {
    setForm((prev) => ({
      ...prev,
      skills: { items: prev.skills.items.filter((s) => s !== skill) },
    }));
  };

  const addItem = (section: keyof FormState, emptyItem: any) => {
    setForm((prev) => ({
      ...prev,
      [section]: { items: [...(prev[section] as any).items, emptyItem] },
    }));
  };

  const updateItem = (section: keyof FormState, index: number, field: string, value: string) => {
    setForm((prev) => {
      const newItems = [...(prev[section] as any).items];
      newItems[index] = { ...newItems[index], [field]: value };
      return { ...prev, [section]: { items: newItems } };
    });
  };

  const removeItem = (section: keyof FormState, index: number) => {
    setForm((prev) => {
      const newItems = [...(prev[section] as any).items];
      newItems.splice(index, 1);
      return { ...prev, [section]: { items: newItems } };
    });
  };

  const handleSubmit = async () => {
    if (!form.title.trim()) {
      toast.error("Resume title is required");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        title: form.title,
        template_name: form.template_name,
        personal_info: form.personal_info,
        skills: form.skills,
        education: form.education,
        work_experience: form.work_experience,
        projects: form.projects,
        certifications: form.certifications,
      };

      let resume;
      if (isEditing && resumeId) {
        resume = await resumeApi.update(resumeId, payload);
      } else {
        resume = await resumeApi.create(payload);
      }

      toast.success(isEditing ? "Resume updated!" : "Resume created!");
      navigate(`/career-tools/resumes/${resume.id}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Failed to save resume"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageShell
      actions={
        <Button disabled={saving} onClick={handleSubmit}>
          {saving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          {isEditing ? "Update" : "Create"} Resume
        </Button>
      }
      description="Fill in your details to build a professional resume."
      eyebrow="Career Tools"
      title={isEditing ? "Edit Resume" : "New Resume"}
    >
      {/* Resume Title */}
      <div className="atlas-panel space-y-4 p-6">
        <p className="type-kicker">Resume Title</p>
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            placeholder="e.g., Software Engineer Resume"
            value={form.title}
            onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
          />
        </div>
      </div>

      {/* Personal Info */}
      <div className="atlas-panel space-y-4 p-6">
        <p className="type-kicker">Personal Information</p>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              placeholder="Ahmed Mohamed"
              value={form.personal_info.name}
              onChange={(e) => updatePersonal("name", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              placeholder="ahmed@example.com"
              type="email"
              value={form.personal_info.email}
              onChange={(e) => updatePersonal("email", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone</Label>
            <Input
              id="phone"
              placeholder="+20 123 456 7890"
              value={form.personal_info.phone}
              onChange={(e) => updatePersonal("phone", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              placeholder="Cairo, Egypt"
              value={form.personal_info.location}
              onChange={(e) => updatePersonal("location", e.target.value)}
            />
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="linkedin">LinkedIn</Label>
            <Input
              id="linkedin"
              placeholder="linkedin.com/in/username"
              value={form.personal_info.linkedin}
              onChange={(e) => updatePersonal("linkedin", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="github">GitHub</Label>
            <Input
              id="github"
              placeholder="github.com/username"
              value={form.personal_info.github}
              onChange={(e) => updatePersonal("github", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="portfolio">Portfolio</Label>
            <Input
              id="portfolio"
              placeholder="yourwebsite.com"
              value={form.personal_info.portfolio}
              onChange={(e) => updatePersonal("portfolio", e.target.value)}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="summary">Professional Summary</Label>
          <Textarea
            id="summary"
            placeholder="Brief overview of your career and key skills..."
            rows={4}
            value={form.personal_info.summary}
            onChange={(e) => updatePersonal("summary", e.target.value)}
          />
        </div>
      </div>

      {/* Skills */}
      <div className="atlas-panel space-y-4 p-6">
        <p className="type-kicker">Skills</p>
        <div className="flex gap-2">
          <Input
            placeholder="Add a skill..."
            value={form.skillInput}
            onChange={(e) => setForm((prev) => ({ ...prev, skillInput: e.target.value }))}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addSkill();
              }
            }}
          />
          <Button onClick={addSkill} type="button" variant="outline">
            Add
          </Button>
        </div>
        {form.skills.items.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {form.skills.items.map((skill) => (
              <button
                className="inline-flex items-center gap-1 rounded-full border border-border/70 bg-background/60 px-3 py-1.5 text-sm transition-smooth hover:border-destructive/50 hover:bg-destructive/10 hover:text-destructive"
                key={skill}
                onClick={() => removeSkill(skill)}
                type="button"
              >
                {skill} ×
              </button>
            ))}
          </div>
        ) : null}
      </div>

      {/* Education */}
      <div className="atlas-panel space-y-4 p-6">
        <div className="flex items-center justify-between">
          <p className="type-kicker">Education</p>
          <Button onClick={() => addItem('education', { degree: '', field: '', institution: '', dates: '', coursework: '' })} size="sm" variant="outline">Add Education</Button>
        </div>
        {form.education.items.map((edu, idx) => (
          <div key={idx} className="grid gap-4 rounded-md border p-4 md:grid-cols-2 relative">
            <Button className="absolute right-2 top-2" size="icon" variant="ghost" onClick={() => removeItem('education', idx)}>×</Button>
            <Input placeholder="Degree (e.g. B.Sc)" value={edu.degree} onChange={(e) => updateItem('education', idx, 'degree', e.target.value)} />
            <Input placeholder="Major / Field" value={edu.field} onChange={(e) => updateItem('education', idx, 'field', e.target.value)} />
            <Input placeholder="University" value={edu.institution} onChange={(e) => updateItem('education', idx, 'institution', e.target.value)} />
            <Input placeholder="Year (e.g. 2024)" value={edu.dates} onChange={(e) => updateItem('education', idx, 'dates', e.target.value)} />
            <Input className="md:col-span-2" placeholder="Relevant Coursework" value={edu.coursework} onChange={(e) => updateItem('education', idx, 'coursework', e.target.value)} />
          </div>
        ))}
      </div>

      {/* Internship / Experience */}
      <div className="atlas-panel space-y-4 p-6">
        <div className="flex items-center justify-between">
          <p className="type-kicker">Internship / Experience</p>
          <Button onClick={() => addItem('work_experience', { company: '', role: '', location: '', start_date: '', end_date: '', description: '' })} size="sm" variant="outline">Add Internship</Button>
        </div>
        {form.work_experience.items.map((exp, idx) => (
          <div key={idx} className="grid gap-4 rounded-md border p-4 md:grid-cols-2 relative">
            <Button className="absolute right-2 top-2" size="icon" variant="ghost" onClick={() => removeItem('work_experience', idx)}>×</Button>
            <Input placeholder="Company" value={exp.company} onChange={(e) => updateItem('work_experience', idx, 'company', e.target.value)} />
            <Input placeholder="Role (e.g. Intern)" value={exp.role} onChange={(e) => updateItem('work_experience', idx, 'role', e.target.value)} />
            <Input placeholder="City, Country" value={exp.location} onChange={(e) => updateItem('work_experience', idx, 'location', e.target.value)} />
            <div className="flex gap-2">
              <Input placeholder="Start (MMM YYYY)" value={exp.start_date} onChange={(e) => updateItem('work_experience', idx, 'start_date', e.target.value)} />
              <Input placeholder="End (MMM YYYY)" value={exp.end_date} onChange={(e) => updateItem('work_experience', idx, 'end_date', e.target.value)} />
            </div>
            <Textarea className="md:col-span-2" placeholder="Description / Achievements (use newlines for bullets)" value={exp.description} onChange={(e) => updateItem('work_experience', idx, 'description', e.target.value)} />
          </div>
        ))}
      </div>

      {/* Projects */}
      <div className="atlas-panel space-y-4 p-6">
        <div className="flex items-center justify-between">
          <p className="type-kicker">Projects</p>
          <Button onClick={() => addItem('projects', { title: '', technologies: '', description: '' })} size="sm" variant="outline">Add Project</Button>
        </div>
        {form.projects.items.map((proj, idx) => (
          <div key={idx} className="grid gap-4 rounded-md border p-4 md:grid-cols-2 relative">
            <Button className="absolute right-2 top-2" size="icon" variant="ghost" onClick={() => removeItem('projects', idx)}>×</Button>
            <Input placeholder="Project Title" value={proj.title} onChange={(e) => updateItem('projects', idx, 'title', e.target.value)} />
            <Input placeholder="Technologies (comma separated)" value={proj.technologies} onChange={(e) => updateItem('projects', idx, 'technologies', e.target.value)} />
            <Textarea className="md:col-span-2" placeholder="Project Description" value={proj.description} onChange={(e) => updateItem('projects', idx, 'description', e.target.value)} />
          </div>
        ))}
      </div>

      {/* Certifications */}
      <div className="atlas-panel space-y-4 p-6">
        <div className="flex items-center justify-between">
          <p className="type-kicker">Certifications</p>
          <Button onClick={() => addItem('certifications', { name: '', issuer: '', date: '' })} size="sm" variant="outline">Add Certification</Button>
        </div>
        {form.certifications.items.map((cert, idx) => (
          <div key={idx} className="grid gap-4 rounded-md border p-4 md:grid-cols-3 relative">
            <Button className="absolute right-2 top-2" size="icon" variant="ghost" onClick={() => removeItem('certifications', idx)}>×</Button>
            <Input placeholder="Certification Name" value={cert.name} onChange={(e) => updateItem('certifications', idx, 'name', e.target.value)} />
            <Input placeholder="Issuer" value={cert.issuer} onChange={(e) => updateItem('certifications', idx, 'issuer', e.target.value)} />
            <Input placeholder="Year" value={cert.date} onChange={(e) => updateItem('certifications', idx, 'date', e.target.value)} />
          </div>
        ))}
      </div>
    </PageShell>
  );
}
