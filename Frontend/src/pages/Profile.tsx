import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { User, Briefcase, Award, Save, X, Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { userApi, UserSkill, Skill, ApiError } from "@/lib/api";

export default function Profile() {
  const { toast } = useToast();
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loadingSkills, setLoadingSkills] = useState(true);
  const [userSkills, setUserSkills] = useState<UserSkill[]>([]);
  const [allSkills, setAllSkills] = useState<Skill[]>([]);

  const [formData, setFormData] = useState({
    username: "",
    full_name: "",
    phone_number: "",
    preferred_language: "en" as "en" | "ar",
    timezone: "Africa/Cairo",
  });

  // Initialize form data from user when loaded
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || "",
        full_name: user.full_name || "",
        phone_number: user.phone_number || "",
        preferred_language: (user.preferred_language as "en" | "ar") || "en",
        timezone: user.timezone || "Africa/Cairo",
      });
    }
  }, [user]);

  const [newSkill, setNewSkill] = useState("");
  const [skillType, setSkillType] = useState<"technical" | "soft">("technical");

  // Load user skills and available skills on mount
  useEffect(() => {
    const loadData = async () => {
      setLoadingSkills(true);
      try {
        const [skillsResponse, allSkillsResponse] = await Promise.all([
          userApi.getSkills(),
          userApi.getAllSkills(),
        ]);
        setUserSkills(skillsResponse);
        setAllSkills(allSkillsResponse);
      } catch (error) {
        console.error('Error loading skills:', error);
        toast({
          title: "Error loading skills",
          description: "Could not load your skills. Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoadingSkills(false);
      }
    };

    loadData();
  }, [toast]);

  // Separate skills by category (technical vs soft)
  const technicalSkills = userSkills.filter(us =>
    us.skill.category?.toLowerCase() !== 'soft' && us.skill.category?.toLowerCase() !== 'soft skills'
  );
  const softSkills = userSkills.filter(us =>
    us.skill.category?.toLowerCase() === 'soft' || us.skill.category?.toLowerCase() === 'soft skills'
  );

  // Calculate completion percentage based on filled fields
  const calculateCompletion = () => {
    let filled = 0;
    let total = 5; // formData fields

    if (formData.username) filled++;
    if (formData.full_name) filled++;
    if (formData.phone_number) filled++;
    if (formData.preferred_language) filled++;
    if (formData.timezone) filled++;

    // Add skills contribution
    if (userSkills.length > 0) filled++;
    total++;

    return Math.round((filled / total) * 100);
  };

  const completionPercentage = calculateCompletion();

  const addSkill = async () => {
    if (!newSkill.trim()) return;

    // Find skill from allSkills or create a placeholder
    const existingSkill = allSkills.find(
      s => s.name.toLowerCase() === newSkill.toLowerCase()
    );

    if (!existingSkill) {
      toast({
        title: "Skill not found",
        description: "This skill is not in our database yet. Try selecting from suggestions.",
        variant: "destructive",
      });
      return;
    }

    try {
      const newUserSkill = await userApi.addSkill(existingSkill.id, 3); // Default proficiency 3
      setUserSkills(prev => [...prev, newUserSkill]);
      setNewSkill("");
      toast({
        title: "Skill added",
        description: `${existingSkill.name} has been added to your profile.`,
      });
    } catch (error) {
      if (error instanceof ApiError) {
        toast({
          title: "Could not add skill",
          description: "This skill may already be in your profile.",
          variant: "destructive",
        });
      }
    }
  };

  const removeSkill = async (userSkillId: string) => {
    try {
      await userApi.removeSkill(userSkillId);
      setUserSkills(prev => prev.filter(us => us.id !== userSkillId));
      toast({
        title: "Skill removed",
        description: "The skill has been removed from your profile.",
      });
    } catch (error) {
      toast({
        title: "Could not remove skill",
        description: "Please try again later.",
        variant: "destructive",
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await userApi.updateProfile({
        username: formData.username,
        full_name: formData.full_name,
        phone_number: formData.phone_number,
        preferred_language: formData.preferred_language,
        timezone: formData.timezone,
      });
      await refreshUser();
      toast({
        title: "Profile updated!",
        description: "Your information has been saved successfully.",
      });
    } catch (error) {
      toast({
        title: "Error updating profile",
        description: "Could not save your profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Your Profile</h1>
        <p className="text-muted-foreground text-lg">
          Welcome, {user?.full_name || user?.username || 'User'}! Complete your profile to get personalized recommendations
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
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  value={user?.email || ''}
                  disabled
                  className="bg-muted"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  placeholder="Your username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  placeholder="Your full name"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phoneNumber">Phone Number</Label>
                <Input
                  id="phoneNumber"
                  placeholder="+201234567890"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="language">Preferred Language</Label>
                <Select
                  value={formData.preferred_language}
                  onValueChange={(value: "en" | "ar") => setFormData({ ...formData, preferred_language: value })}
                >
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover">
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="ar">Arabic</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Select
                  value={formData.timezone}
                  onValueChange={(value) => setFormData({ ...formData, timezone: value })}
                >
                  <SelectTrigger id="timezone">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover">
                    <SelectItem value="Africa/Cairo">Africa/Cairo (EET)</SelectItem>
                    <SelectItem value="Europe/London">Europe/London (GMT)</SelectItem>
                    <SelectItem value="America/New_York">America/New York (EST)</SelectItem>
                    <SelectItem value="Asia/Dubai">Asia/Dubai (GST)</SelectItem>
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
            <CardDescription>Add your technical and soft skills from your profile</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {loadingSkills ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading skills...</span>
              </div>
            ) : (
              <>
                {/* Technical Skills */}
                <div className="space-y-3">
                  <Label>Technical Skills ({technicalSkills.length})</Label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {technicalSkills.map((userSkill) => (
                      <Badge key={userSkill.id} variant="secondary" className="text-sm">
                        {userSkill.skill.name}
                        {userSkill.is_verified && <span className="ml-1 text-green-500">✓</span>}
                        <button
                          type="button"
                          onClick={() => removeSkill(userSkill.id)}
                          className="ml-2 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                    {technicalSkills.length === 0 && (
                      <span className="text-sm text-muted-foreground">No technical skills added yet</span>
                    )}
                  </div>
                </div>

                {/* Soft Skills */}
                <div className="space-y-3">
                  <Label>Soft Skills ({softSkills.length})</Label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {softSkills.map((userSkill) => (
                      <Badge key={userSkill.id} variant="secondary" className="text-sm">
                        {userSkill.skill.name}
                        {userSkill.is_verified && <span className="ml-1 text-green-500">✓</span>}
                        <button
                          type="button"
                          onClick={() => removeSkill(userSkill.id)}
                          className="ml-2 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                    {softSkills.length === 0 && (
                      <span className="text-sm text-muted-foreground">No soft skills added yet</span>
                    )}
                  </div>
                </div>

                {/* Add new skill */}
                <div className="space-y-3">
                  <Label>Add a Skill</Label>
                  <div className="flex gap-2">
                    <Select value={skillType} onValueChange={(value: "technical" | "soft") => setSkillType(value)}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-popover">
                        <SelectItem value="technical">Technical</SelectItem>
                        <SelectItem value="soft">Soft</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder="Type skill name..."
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addSkill();
                        }
                      }}
                      list="skill-suggestions"
                    />
                    <datalist id="skill-suggestions">
                      {allSkills
                        .filter(s => s.name.toLowerCase().includes(newSkill.toLowerCase()))
                        .slice(0, 10)
                        .map(s => (
                          <option key={s.id} value={s.name} />
                        ))
                      }
                    </datalist>
                    <Button type="button" onClick={addSkill} variant="outline">
                      Add
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" className="gradient-primary" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Profile
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
