import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { User, Briefcase, Award, Target, Save, X } from "lucide-react";

export default function Profile() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    jobTitle: "Frontend Developer",
    industry: "technology",
    experience: "3-5",
    education: "bachelor",
    technicalSkills: ["React", "TypeScript", "Node.js", "Python"],
    softSkills: ["Communication", "Problem Solving", "Teamwork"],
    careerObjectives: "Transition into a full-stack development role with focus on scalable web applications",
  });

  const [newSkill, setNewSkill] = useState("");
  const [skillType, setSkillType] = useState<"technical" | "soft">("technical");

  const completionPercentage = 85; // Calculate based on filled fields

  const addSkill = () => {
    if (!newSkill.trim()) return;
    
    if (skillType === "technical") {
      setFormData({
        ...formData,
        technicalSkills: [...formData.technicalSkills, newSkill],
      });
    } else {
      setFormData({
        ...formData,
        softSkills: [...formData.softSkills, newSkill],
      });
    }
    setNewSkill("");
  };

  const removeSkill = (skill: string, type: "technical" | "soft") => {
    if (type === "technical") {
      setFormData({
        ...formData,
        technicalSkills: formData.technicalSkills.filter((s) => s !== skill),
      });
    } else {
      setFormData({
        ...formData,
        softSkills: formData.softSkills.filter((s) => s !== skill),
      });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      toast({
        title: "Profile updated!",
        description: "Your information has been saved successfully.",
      });
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Your Profile</h1>
        <p className="text-muted-foreground text-lg">
          Complete your profile to get personalized recommendations
        </p>
      </div>

      {/* Profile Completion Card */}
      <Card className="gradient-primary text-primary-foreground">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            Profile Completion
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Complete your profile to unlock all features</span>
            <span className="text-2xl font-bold">{completionPercentage}%</span>
          </div>
          <Progress value={completionPercentage} className="h-3 bg-primary-foreground/20" />
        </CardContent>
      </Card>

      {/* Profile Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Basic Information
            </CardTitle>
            <CardDescription>Tell us about your current professional status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="jobTitle">Current Job Title</Label>
                <Input
                  id="jobTitle"
                  placeholder="e.g., Software Developer"
                  value={formData.jobTitle}
                  onChange={(e) => setFormData({ ...formData, jobTitle: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="industry">Industry Sector</Label>
                <Select value={formData.industry} onValueChange={(value) => setFormData({ ...formData, industry: value })}>
                  <SelectTrigger id="industry">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover">
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="retail">Retail</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="experience">Years of Experience</Label>
                <Select value={formData.experience} onValueChange={(value) => setFormData({ ...formData, experience: value })}>
                  <SelectTrigger id="experience">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover">
                    <SelectItem value="0-1">0-1 years</SelectItem>
                    <SelectItem value="1-3">1-3 years</SelectItem>
                    <SelectItem value="3-5">3-5 years</SelectItem>
                    <SelectItem value="5-10">5-10 years</SelectItem>
                    <SelectItem value="10+">10+ years</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="education">Education Level</Label>
                <Select value={formData.education} onValueChange={(value) => setFormData({ ...formData, education: value })}>
                  <SelectTrigger id="education">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover">
                    <SelectItem value="high-school">High School</SelectItem>
                    <SelectItem value="associate">Associate Degree</SelectItem>
                    <SelectItem value="bachelor">Bachelor's Degree</SelectItem>
                    <SelectItem value="master">Master's Degree</SelectItem>
                    <SelectItem value="phd">PhD</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Skills */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="h-5 w-5" />
              Skills & Expertise
            </CardTitle>
            <CardDescription>Add your technical and soft skills</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Technical Skills */}
            <div className="space-y-3">
              <Label>Technical Skills</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {formData.technicalSkills.map((skill) => (
                  <Badge key={skill} variant="secondary" className="text-sm">
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(skill, "technical")}
                      className="ml-2 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Add a technical skill"
                  value={skillType === "technical" ? newSkill : ""}
                  onChange={(e) => {
                    setSkillType("technical");
                    setNewSkill(e.target.value);
                  }}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addSkill();
                    }
                  }}
                />
                <Button type="button" onClick={addSkill} variant="outline">
                  Add
                </Button>
              </div>
            </div>

            {/* Soft Skills */}
            <div className="space-y-3">
              <Label>Soft Skills</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {formData.softSkills.map((skill) => (
                  <Badge key={skill} variant="secondary" className="text-sm">
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(skill, "soft")}
                      className="ml-2 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Add a soft skill"
                  value={skillType === "soft" ? newSkill : ""}
                  onChange={(e) => {
                    setSkillType("soft");
                    setNewSkill(e.target.value);
                  }}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addSkill();
                    }
                  }}
                />
                <Button type="button" onClick={addSkill} variant="outline">
                  Add
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Career Objectives */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Career Objectives
            </CardTitle>
            <CardDescription>Describe your career goals and aspirations (max 500 characters)</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="What are your career goals? What kind of role are you aiming for?"
              className="min-h-32"
              maxLength={500}
              value={formData.careerObjectives}
              onChange={(e) => setFormData({ ...formData, careerObjectives: e.target.value })}
            />
            <p className="text-xs text-muted-foreground mt-2">
              {formData.careerObjectives.length}/500 characters
            </p>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" className="gradient-primary" disabled={loading}>
            <Save className="mr-2 h-4 w-4" />
            {loading ? "Saving..." : "Save Profile"}
          </Button>
        </div>
      </form>
    </div>
  );
}
