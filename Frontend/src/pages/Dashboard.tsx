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
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();

  // Get first name for greeting
  const firstName = user?.full_name?.split(' ')[0] || user?.username || 'User';

  // TODO: Replace with real data from API
  // Mock data
  const stats = [
    {
      title: "Roadmap Progress",
      value: "68%",
      icon: Target,
      change: "+12% this month",
      color: "text-primary",
    },
    {
      title: "Milestones Completed",
      value: "24/35",
      icon: Award,
      change: "3 this week",
      color: "text-success",
    },
    {
      title: "Learning Streak",
      value: "12 days",
      icon: Zap,
      change: "Personal best!",
      color: "text-accent",
    },
    {
      title: "Hours This Week",
      value: "18h",
      icon: BookOpen,
      change: "Goal: 20h",
      color: "text-info",
    },
  ];

  const recentMilestones = [
    {
      title: "React Fundamentals",
      phase: "Frontend Development",
      completedAt: "2 days ago",
      skills: ["React", "JSX", "Components"],
    },
    {
      title: "API Integration Basics",
      phase: "Backend Basics",
      completedAt: "5 days ago",
      skills: ["REST", "HTTP", "JSON"],
    },
    {
      title: "Git & Version Control",
      phase: "Development Tools",
      completedAt: "1 week ago",
      skills: ["Git", "GitHub", "Collaboration"],
    },
  ];

  const upcomingMilestones = [
    {
      title: "Advanced React Patterns",
      phase: "Frontend Development",
      estimatedTime: "8 hours",
      priority: "high",
    },
    {
      title: "State Management with Redux",
      phase: "Frontend Development",
      estimatedTime: "12 hours",
      priority: "medium",
    },
  ];

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
        <Link to="/assessment">
          <Button size="lg" className="gradient-primary text-primary-foreground">
            <Target className="mr-2 h-5 w-5" />
            Start Assessment
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
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
                <span className="text-sm font-bold text-primary">68%</span>
              </div>
              <Progress value={68} className="h-3" />
              <p className="text-xs text-muted-foreground mt-2">
                24 of 35 milestones completed • Estimated 3 months remaining
              </p>
            </div>

            {/* Phase Progress */}
            <div className="space-y-4">
              <h4 className="font-semibold text-sm">Phase Progress</h4>
              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">Frontend Development</span>
                    <Badge variant="outline" className="text-success border-success">
                      Completed
                    </Badge>
                  </div>
                  <Progress value={100} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">Backend Basics</span>
                    <span className="text-xs text-muted-foreground">75%</span>
                  </div>
                  <Progress value={75} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">Database Design</span>
                    <span className="text-xs text-muted-foreground">40%</span>
                  </div>
                  <Progress value={40} className="h-2" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions & Achievements */}
        <div className="space-y-6">
          {/* Achievement Card */}
          <Card className="gradient-accent text-accent-foreground">
            <CardHeader>
              <CardTitle className="flex items-center text-base">
                <Award className="mr-2 h-5 w-5" />
                Recent Achievement
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-4xl">🔥</div>
                <h4 className="font-bold">12-Day Streak!</h4>
                <p className="text-sm opacity-90">
                  You're on fire! Keep learning every day to maintain your streak.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Calendar Widget */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-base">
                <Calendar className="mr-2 h-5 w-5" />
                This Week's Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-7 gap-2">
                {["M", "T", "W", "T", "F", "S", "S"].map((day, i) => (
                  <div key={i} className="text-center">
                    <div className="text-xs text-muted-foreground mb-1">{day}</div>
                    <div
                      className={`h-8 w-8 rounded-md flex items-center justify-center text-xs font-medium ${
                        i < 5
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {i < 5 ? "✓" : ""}
                    </div>
                  </div>
                ))}
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
            {recentMilestones.map((milestone, i) => (
              <div key={i} className="flex items-start space-x-4 p-4 rounded-lg bg-muted/50">
                <div className="h-10 w-10 rounded-full bg-success/10 flex items-center justify-center flex-shrink-0">
                  <Award className="h-5 w-5 text-success" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-sm mb-1">{milestone.title}</h4>
                  <p className="text-xs text-muted-foreground mb-2">
                    {milestone.phase} • {milestone.completedAt}
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {milestone.skills.map((skill) => (
                      <Badge key={skill} variant="secondary" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Up Next */}
        <Card>
          <CardHeader>
            <CardTitle>Up Next</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {upcomingMilestones.map((milestone, i) => (
              <div key={i} className="flex items-start space-x-4 p-4 rounded-lg border-2 border-dashed">
                <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Target className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-sm">{milestone.title}</h4>
                    <Badge
                      variant={milestone.priority === "high" ? "destructive" : "secondary"}
                      className="text-xs"
                    >
                      {milestone.priority}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mb-3">
                    {milestone.phase} • ~{milestone.estimatedTime}
                  </p>
                  <Button size="sm" variant="outline" className="w-full">
                    Start Learning
                  </Button>
                </div>
              </div>
            ))}
            <Link to="/roadmap">
              <Button variant="ghost" className="w-full">
                View All Milestones
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
