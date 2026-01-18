import { useEffect, useState, useMemo, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Target,
  TrendingUp,
  Calendar,
  Award,
  ArrowRight,
  Zap,
  BookOpen,
  Loader2,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { roadmapApi, type Roadmap, type RoadmapMilestone } from "@/lib/api";
import { toast } from "sonner";

interface RoadmapStats {
  total_phases: number;
  completed_phases: number;
  total_milestones: number;
  completed_milestones: number;
  estimated_total_hours: number;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [stats, setStats] = useState<RoadmapStats | null>(null);
  const [loading, setLoading] = useState(true);

  // Get first name for greeting
  const firstName = user?.full_name?.split(' ')[0] || user?.username || 'User';

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);

      // Fetch active or in-progress roadmaps
      const roadmapsRes = await roadmapApi.list({ status: 'in_progress' });
      let activeRoadmaps = roadmapsRes.results || [];

      // If no in-progress, try active status
      if (activeRoadmaps.length === 0) {
        const activeRes = await roadmapApi.list({ status: 'active' });
        activeRoadmaps = activeRes.results || [];
      }

      if (activeRoadmaps.length > 0) {
        // Fetch full roadmap with hierarchy
        const fullRoadmap = await roadmapApi.get(activeRoadmaps[0].id);
        setRoadmap(fullRoadmap);

        // Fetch roadmap statistics
        const statsData = await roadmapApi.getStats(fullRoadmap.id);
        setStats(statsData);
      }
    } catch (error: any) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Calculate recent and upcoming milestones from roadmap
  const allMilestones = useMemo(() => {
    const milestones: Array<RoadmapMilestone & { phaseName?: string }> = [];
    roadmap?.phases?.forEach(phase => {
      phase.milestones?.forEach(milestone => {
        milestones.push({ ...milestone, phaseName: phase.title });
      });
    });
    return milestones;
  }, [roadmap?.phases]);

  const completedMilestones = useMemo(
    () =>
      allMilestones
        .filter(m => m.status === 'completed')
        .sort((a, b) => {
          if (!a.completed_at || !b.completed_at) return 0;
          return new Date(b.completed_at).getTime() - new Date(a.completed_at).getTime();
        })
        .slice(0, 3),
    [allMilestones]
  );

  const upcomingMilestones = useMemo(
    () =>
      allMilestones
        .filter(m => m.status === 'not_started' || m.status === 'in_progress')
        .slice(0, 2),
    [allMilestones]
  );

  const dashboardStats = [
    {
      title: "Roadmap Progress",
      value: roadmap ? `${parseFloat(roadmap.completion_percentage).toFixed(0)}%` : "0%",
      icon: Target,
      change: roadmap ? `${roadmap.completed_phases || 0}/${roadmap.total_phases || 0} phases` : "No active roadmap",
      color: "text-primary",
    },
    {
      title: "Milestones Completed",
      value: stats ? `${stats.completed_milestones}/${stats.total_milestones}` : "0/0",
      icon: Award,
      change: completedMilestones.length > 0 ? `${completedMilestones.length} recently` : "None yet",
      color: "text-success",
    },
    {
      title: "Learning Time",
      value: stats ? `${Math.round(stats.estimated_total_hours)}h` : "0h",
      icon: BookOpen,
      change: roadmap ? `${roadmap.weekly_hours_commitment}h/week goal` : "Set goal in roadmap",
      color: "text-info",
    },
    {
      title: "Total Phases",
      value: stats ? stats.total_phases.toString() : "0",
      icon: Zap,
      change: roadmap?.status === 'in_progress' ? "Active" : roadmap?.status || "Not started",
      color: "text-accent",
    },
  ];

  const formatTimeAgo = (dateString?: string) => {
    if (!dateString) return 'Recently';

    const now = new Date();
    const past = new Date(dateString);
    const diffMs = now.getTime() - past.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold mb-2">Welcome back, {firstName}!</h1>
          <p className="text-muted-foreground text-lg">
            Track your progress and continue your learning journey
          </p>
        </div>
        {!roadmap && (
          <Link to="/roadmap">
            <Button size="lg" className="gradient-primary text-primary-foreground">
              <Target className="mr-2 h-5 w-5" />
              Create Roadmap
            </Button>
          </Link>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardStats.map((stat) => (
          <Card key={stat.title} className="transition-smooth hover:shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-5 w-5 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-1">{stat.value}</div>
              <p className="text-xs text-muted-foreground flex items-center">
                <TrendingUp className="mr-1 h-3 w-3" />
                {stat.change}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {roadmap ? (
        <>
          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Overall Progress */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Your Learning Roadmap</span>
                  <Link to="/roadmap">
                    <Button variant="ghost" size="sm">
                      View Full Roadmap
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Progress Overview */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Overall Progress</span>
                    <span className="text-sm font-bold text-primary">
                      {parseFloat(roadmap.completion_percentage).toFixed(0)}%
                    </span>
                  </div>
                  <Progress value={parseFloat(roadmap.completion_percentage)} className="h-3" />
                  <p className="text-xs text-muted-foreground mt-2">
                    {stats?.completed_milestones || 0} of {stats?.total_milestones || 0} milestones completed • {roadmap.estimated_duration_weeks} weeks total
                  </p>
                </div>

                {/* Phase Progress */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-sm">Phase Progress</h4>
                  <div className="space-y-3">
                    {roadmap.phases?.slice(0, 3).map((phase) => (
                      <div key={phase.id}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm">{phase.title}</span>
                          {phase.status === 'completed' ? (
                            <Badge variant="outline" className="text-success border-success bg-success/10">
                              Completed
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">
                              {parseFloat(phase.completion_percentage || '0').toFixed(0)}%
                            </span>
                          )}
                        </div>
                        <Progress value={parseFloat(phase.completion_percentage || '0')} className="h-2" />
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions & Achievements */}
            <div className="space-y-6">
              {/* Roadmap Info Card */}
              <Card className="gradient-accent text-accent-foreground">
                <CardHeader>
                  <CardTitle className="flex items-center text-base">
                    <Target className="mr-2 h-5 w-5" />
                    Active Roadmap
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-4xl">🎯</div>
                    <h4 className="font-bold">{roadmap.target_career}</h4>
                    <p className="text-sm opacity-90">
                      {roadmap.description?.slice(0, 80)}...
                    </p>
                    <Badge variant="secondary" className="capitalize">
                      {roadmap.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Week Activity Placeholder */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-base">
                    <Calendar className="mr-2 h-5 w-5" />
                    This Week's Activity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-muted-foreground text-center py-4">
                    Activity tracking coming soon
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Recent & Upcoming Milestones */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recently Completed */}
            <Card>
              <CardHeader>
                <CardTitle>Recently Completed</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {completedMilestones.length > 0 ? (
                  completedMilestones.map((milestone) => (
                    <div key={milestone.id} className="flex items-start space-x-4 p-4 rounded-lg bg-muted/50">
                      <div className="h-10 w-10 rounded-full bg-success/10 flex items-center justify-center flex-shrink-0">
                        <Award className="h-5 w-5 text-success" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-sm mb-1">{milestone.title}</h4>
                        <p className="text-xs text-muted-foreground mb-2">
                          {(milestone as any).phaseName} • {formatTimeAgo(milestone.completed_at)}
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {milestone.skills?.slice(0, 3).map((skill) => (
                            <Badge key={skill} variant="secondary" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Award className="h-12 w-12 mx-auto mb-2 opacity-20" />
                    <p className="text-sm">No milestones completed yet</p>
                    <p className="text-xs mt-1">Start working on your roadmap!</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Up Next */}
            <Card>
              <CardHeader>
                <CardTitle>Up Next</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {upcomingMilestones.length > 0 ? (
                  upcomingMilestones.map((milestone) => (
                    <div key={milestone.id} className="flex items-start space-x-4 p-4 rounded-lg border-2 border-dashed">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Target className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-sm">{milestone.title}</h4>
                          {milestone.is_required && (
                            <Badge variant="secondary" className="text-xs">
                              Required
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">
                          {(milestone as any).phaseName} • ~{milestone.estimated_duration_hours}h
                        </p>
                        <Link to="/roadmap">
                          <Button size="sm" variant="outline" className="w-full">
                            Start Learning
                          </Button>
                        </Link>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Target className="h-12 w-12 mx-auto mb-2 opacity-20" />
                    <p className="text-sm">All milestones completed!</p>
                    <p className="text-xs mt-1">🎉 Great job!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      ) : (
        /* No Roadmap State */
        <Card className="border-dashed">
          <CardContent className="py-12">
            <div className="text-center space-y-4">
              <div className="mx-auto h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Target className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">No Active Roadmap</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Create your personalized learning roadmap to start tracking your progress and achieving your career goals.
                </p>
              </div>
              <div className="flex gap-3 justify-center">
                <Link to="/assessment">
                  <Button variant="outline">Take Assessment First</Button>
                </Link>
                <Link to="/roadmap">
                  <Button className="gradient-primary">
                    <Target className="mr-2 h-4 w-4" />
                    Create Roadmap
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
