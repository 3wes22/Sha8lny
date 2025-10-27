import Navigation from "@/components/Navigation";
import StatCard from "@/components/StatCard";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Users, 
  TrendingUp, 
  Award, 
  BookOpen,
  Plus,
  Search,
  Download,
  BarChart3,
  Target,
  Clock
} from "lucide-react";

const Corporate = () => {
  const teamStats = {
    totalEmployees: 250,
    activelearners: 187,
    coursesCompleted: 542,
    avgSkillScore: 78
  };

  const employees = [
    {
      name: "Sarah Ahmed",
      role: "Frontend Developer",
      progress: 75,
      coursesCompleted: 8,
      lastActive: "2 hours ago",
      status: "active"
    },
    {
      name: "Mohamed Hassan",
      role: "Backend Developer",
      progress: 60,
      coursesCompleted: 6,
      lastActive: "1 day ago",
      status: "active"
    },
    {
      name: "Fatima Ali",
      role: "Full Stack Developer",
      progress: 85,
      coursesCompleted: 12,
      lastActive: "Today",
      status: "active"
    },
    {
      name: "Omar Khaled",
      role: "DevOps Engineer",
      progress: 45,
      coursesCompleted: 4,
      lastActive: "3 days ago",
      status: "inactive"
    },
  ];

  const learningPaths = [
    {
      title: "Frontend Excellence",
      enrolled: 45,
      completion: 68,
      duration: "3 months"
    },
    {
      title: "Backend Mastery",
      enrolled: 38,
      completion: 55,
      duration: "4 months"
    },
    {
      title: "Cloud Architecture",
      enrolled: 28,
      completion: 42,
      duration: "2 months"
    },
  ];

  const topSkills = [
    { skill: "React", employees: 85, trend: "+12%" },
    { skill: "Node.js", employees: 72, trend: "+8%" },
    { skill: "Python", employees: 68, trend: "+15%" },
    { skill: "AWS", employees: 54, trend: "+20%" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Corporate Dashboard</h1>
            <p className="text-muted-foreground">Manage your team's learning and development</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline">
              <Download size={16} />
              Export Report
            </Button>
            <Button variant="hero">
              <Plus size={16} />
              Add Employee
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard 
            icon={Users} 
            label="Total Employees" 
            value={teamStats.totalEmployees}
            trend="+12 this month"
            trendUp={true}
          />
          <StatCard 
            icon={BookOpen} 
            label="Active Learners" 
            value={teamStats.activelearners}
            trend="75% engagement"
            trendUp={true}
          />
          <StatCard 
            icon={Award} 
            label="Courses Completed" 
            value={teamStats.coursesCompleted}
            trend="+48 this month"
            trendUp={true}
          />
          <StatCard 
            icon={TrendingUp} 
            label="Avg Skill Score" 
            value={`${teamStats.avgSkillScore}%`}
            trend="+5% improvement"
            trendUp={true}
          />
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Employee Management */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Team Members</h2>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={16} />
                  <Input placeholder="Search employees..." className="pl-9" />
                </div>
              </div>

              <div className="space-y-3">
                {employees.map((employee, index) => (
                  <div key={index} className="p-4 border rounded-lg hover:border-primary/50 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex gap-3">
                        <div className="w-10 h-10 bg-gradient-primary rounded-full flex items-center justify-center">
                          <span className="text-primary-foreground font-semibold">
                            {employee.name.split(' ').map(n => n[0]).join('')}
                          </span>
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{employee.name}</h3>
                            <Badge 
                              variant={employee.status === "active" ? "secondary" : "outline"}
                              className="text-xs"
                            >
                              {employee.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">{employee.role}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Last active: {employee.lastActive}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-primary">{employee.progress}%</div>
                        <div className="text-xs text-muted-foreground">Progress</div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">
                        {employee.coursesCompleted} courses completed
                      </span>
                    </div>
                    <Progress value={employee.progress} className="h-2" />
                  </div>
                ))}
              </div>
            </Card>

            {/* Custom Learning Paths */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Learning Paths</h2>
                <Button variant="outline" size="sm">
                  <Plus size={16} />
                  Create Path
                </Button>
              </div>

              <div className="space-y-4">
                {learningPaths.map((path, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold mb-1">{path.title}</h3>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Users size={14} />
                            {path.enrolled} enrolled
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {path.duration}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-secondary">{path.completion}%</div>
                        <div className="text-xs text-muted-foreground">Avg completion</div>
                      </div>
                    </div>
                    <Progress value={path.completion} className="h-2 mb-3" />
                    <Button variant="outline" size="sm" className="w-full">Manage Path</Button>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Analytics Summary */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="text-accent" size={20} />
                <h3 className="font-semibold">Analytics Overview</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-muted-foreground">Weekly Engagement</span>
                    <span className="font-semibold text-secondary">↑ 85%</span>
                  </div>
                  <Progress value={85} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-muted-foreground">Goal Achievement</span>
                    <span className="font-semibold text-secondary">↑ 72%</span>
                  </div>
                  <Progress value={72} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-muted-foreground">Skill Development</span>
                    <span className="font-semibold text-accent">↑ 68%</span>
                  </div>
                  <Progress value={68} className="h-2" />
                </div>
              </div>
            </Card>

            {/* Top Skills */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center gap-2 mb-4">
                <Target className="text-primary" size={20} />
                <h3 className="font-semibold">Top Team Skills</h3>
              </div>
              <div className="space-y-3">
                {topSkills.map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div>
                      <p className="font-medium">{item.skill}</p>
                      <p className="text-xs text-muted-foreground">{item.employees} employees</p>
                    </div>
                    <span className="text-sm font-semibold text-secondary">{item.trend}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* ROI Calculator */}
            <Card className="p-6 shadow-card bg-gradient-secondary text-secondary-foreground">
              <h3 className="font-semibold mb-3">Training ROI</h3>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-sm text-secondary-foreground/90">Investment</span>
                  <span className="font-semibold">EGP 125K</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-secondary-foreground/90">Productivity Gain</span>
                  <span className="font-semibold">+32%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-secondary-foreground/90">Est. ROI</span>
                  <span className="font-bold text-lg">285%</span>
                </div>
              </div>
              <Button variant="accent" className="w-full">
                View Full Report
              </Button>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Corporate;
