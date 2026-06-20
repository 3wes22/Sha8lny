import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { ROUTES } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { userApi, type UserPreferences } from "@/lib/api";
import { PageShell } from "@/shared/components/PageShell";
import { StatePanel } from "@/shared/components/StatePanel";
import { useToast } from "@/hooks/use-toast";

export default function SettingsPage() {
  const { toast } = useToast();
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setLoading(true);
        setPreferences(await userApi.getPreferences());
      } catch {
        toast({
          title: "Settings unavailable",
          description: "Could not load your preferences.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    void loadPreferences();
  }, [toast]);

  const handleToggle = async (key: keyof UserPreferences, value: boolean) => {
    if (!preferences) return;

    try {
      const updated = await userApi.updatePreferences({ [key]: value });
      setPreferences(updated);
    } catch {
      toast({
        title: "Update failed",
        description: "Could not save this setting.",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!preferences) {
    return (
      <StatePanel
        description="The settings surface could not be loaded."
        state="error"
        title="Settings unavailable"
      />
    );
  }

  return (
    <PageShell
      actions={
        <Button asChild variant="outline">
          <Link to={ROUTES.forgotPassword}>Account recovery (MVP stub)</Link>
        </Button>
      }
      description="Keep delivery and privacy settings explicit."
      eyebrow="Settings"
      title="Preferences"
    >
      <div className="atlas-panel p-6">
        <div className="space-y-4">
          {[
            ["email_notifications", "Email notifications"],
            ["push_notifications", "Push notifications"],
            ["weekly_digest", "Weekly digest"],
            ["show_progress", "Show progress publicly"],
          ].map(([key, label]) => (
            <div className="flex items-center justify-between border-b border-border/50 py-3 last:border-b-0" key={key}>
              <div>
                <p className="font-semibold">{label}</p>
                <p className="text-sm text-muted-foreground">Toggle this preference for your account.</p>
              </div>
              <Switch
                checked={Boolean(preferences[key as keyof UserPreferences])}
                onCheckedChange={(checked) => void handleToggle(key as keyof UserPreferences, checked)}
              />
            </div>
          ))}
        </div>
      </div>
    </PageShell>
  );
}
