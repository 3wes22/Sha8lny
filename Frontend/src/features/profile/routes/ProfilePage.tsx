import { useEffect, useState } from "react";
import { Loader2, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/context/AuthContext";
import { ApiError, type Skill, type UserSkill, userApi } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

export default function ProfilePage() {
  const { toast } = useToast();
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [skillsLoading, setSkillsLoading] = useState(true);
  const [userSkills, setUserSkills] = useState<UserSkill[]>([]);
  const [allSkills, setAllSkills] = useState<Skill[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [formData, setFormData] = useState({
    username: "",
    full_name: "",
    phone_number: "",
    preferred_language: "en",
    timezone: "Africa/Cairo",
  });

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || "",
        full_name: user.full_name || "",
        phone_number: user.phone_number || "",
        preferred_language: user.preferred_language || "en",
        timezone: user.timezone || "Africa/Cairo",
      });
    }
  }, [user]);

  useEffect(() => {
    const loadSkills = async () => {
      try {
        setSkillsLoading(true);
        const [skillsResponse, allSkillsResponse] = await Promise.all([
          userApi.getSkills(),
          userApi.getAllSkills(),
        ]);
        setUserSkills(skillsResponse.results ?? []);
        setAllSkills(allSkillsResponse.results ?? []);
      } catch {
        toast({
          title: "Error loading profile",
          description: "Could not load your current skills.",
          variant: "destructive",
        });
      } finally {
        setSkillsLoading(false);
      }
    };

    void loadSkills();
  }, [toast]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      setLoading(true);
      await userApi.updateProfile(formData);
      await refreshUser();
      toast({ title: "Profile updated", description: "Your profile details were saved." });
    } catch {
      toast({
        title: "Update failed",
        description: "Could not save your profile.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddSkill = async () => {
    const matchedSkill = allSkills.find(
      (skill) => skill.name.toLowerCase() === newSkill.trim().toLowerCase(),
    );
    if (!matchedSkill) {
      toast({
        title: "Skill not found",
        description: "Choose a skill that already exists in the system.",
        variant: "destructive",
      });
      return;
    }

    try {
      const addedSkill = await userApi.addSkill(matchedSkill.id, "intermediate");
      setUserSkills((previous) => [...previous, addedSkill]);
      setNewSkill("");
    } catch (error) {
      if (error instanceof ApiError) {
        toast({
          title: "Could not add skill",
          description: "This skill may already be attached to your profile.",
          variant: "destructive",
        });
      }
    }
  };

  const handleRemoveSkill = async (userSkillId: string) => {
    await userApi.removeSkill(userSkillId);
    setUserSkills((previous) => previous.filter((item) => item.id !== userSkillId));
  };

  return (
    <PageShell
      description="Keep identity and skills current so roadmap and job signals stay relevant."
      eyebrow="Profile"
      title={user?.full_name || "Your profile"}
      aside={
        <div className="space-y-4">
          <div className="atlas-panel p-5">
            <p className="type-kicker">Skill signal</p>
            <p className="mt-3 text-3xl font-bold">{userSkills.length}</p>
            <p className="mt-2 text-sm text-muted-foreground">Tracked skills currently connected to your profile.</p>
          </div>
        </div>
      }
    >
      <form className="atlas-panel p-6" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              onChange={(event) => setFormData((previous) => ({ ...previous, username: event.target.value }))}
              value={formData.username}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="full_name">Full name</Label>
            <Input
              id="full_name"
              onChange={(event) => setFormData((previous) => ({ ...previous, full_name: event.target.value }))}
              value={formData.full_name}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone_number">Phone number</Label>
            <Input
              id="phone_number"
              onChange={(event) => setFormData((previous) => ({ ...previous, phone_number: event.target.value }))}
              value={formData.phone_number}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Input
              id="timezone"
              onChange={(event) => setFormData((previous) => ({ ...previous, timezone: event.target.value }))}
              value={formData.timezone}
            />
          </div>
        </div>
        <Button className="mt-5 gradient-primary" disabled={loading} type="submit">
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Save profile
        </Button>
      </form>

      <div className="atlas-panel p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-end">
          <div className="flex-1 space-y-2">
            <Label htmlFor="new_skill">Add skill</Label>
            <Input
              id="new_skill"
              onChange={(event) => setNewSkill(event.target.value)}
              placeholder="Type an exact skill name"
              value={newSkill}
            />
          </div>
          <Button onClick={handleAddSkill} type="button" variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            Add skill
          </Button>
        </div>

        {skillsLoading ? (
          <div className="mt-5 flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading skills...
          </div>
        ) : userSkills.length > 0 ? (
          <div className="mt-5 flex flex-wrap gap-3">
            {userSkills.map((userSkill) => (
              <button
                className="rounded-full border border-border/70 px-4 py-2 text-sm transition-smooth hover:bg-muted/70"
                key={userSkill.id}
                onClick={() => void handleRemoveSkill(userSkill.id)}
                type="button"
              >
                {userSkill.skill.name} · level {userSkill.proficiency_level}
              </button>
            ))}
          </div>
        ) : (
          <StatePanel
            description="Add skills so job matching and roadmap recommendations have better signal."
            state="empty"
            title="No skills attached yet"
          />
        )}
      </div>
    </PageShell>
  );
}
