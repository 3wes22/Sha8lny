import Navigation from "@/components/Navigation";
import StatCard from "@/components/StatCard";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { 
  TrendingUp, 
  BookOpen, 
  Target, 
  Award,
  ArrowRight,
  MessageCircle,
  Calendar,
  Briefcase,
  BarChart3
} from "lucide-react";
import { Link } from "react-router-dom";

const Dashboard = () => {
  const quickActions = [
    { icon: Target, label: "Take Assessment", path: "/assessments", color: "bg-primary/10 text-primary" },
    { icon: BookOpen, label: "Browse Courses", path: "/learning", color: "bg-secondary/10 text-secondary" },
    { icon: Briefcase, label: "Find Jobs", path: "/jobs", color: "bg-accent/10 text-accent" },
    { icon: Award, label: "View Certificates", path: "/profile", color: "bg-purple-100 text-purple-600" },
  ];

  const upcomingCourses = [
    { title: "Advanced React Patterns", progress: 65, nextLesson: "Custom Hooks" },
    { title: "Python for Data Science", progress: 40, nextLesson: "Pandas Basics" },
    { title: "Cloud Architecture", progress: 20, nextLesson: "AWS Fundamentals" },
  ];

  const matchedJobs = [
    { title: "Senior Frontend Developer", company: "Tech Corp", match: 95, location: "Cairo" },
    { title: "Full Stack Engineer", company: "Startup Hub", match: 88, location: "Remote" },
    { title: "React Developer", company: "Digital Agency", match: 85, location: "Alexandria" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Welcome back, Ahmed! 👋</h1>
          <p className="text-muted-foreground">Here's your learning progress and career insights</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard 
            icon={Target} 
            label="Profile Strength" 
            value="85%" 
            trend="+5% this week"
            trendUp={true}
          />
          <StatCard 
            icon={BookOpen} 
            label="Courses In Progress" 
            value="3" 
            trend="2 to complete"
            trendUp={true}
          />
          <StatCard 
            icon={Briefcase} 
            label="Job Matches" 
            value="12" 
            trend="3 new today"
            trendUp={true}
          />
          <StatCard 
            icon={Award} 
            label="Certifications" 
            value="5" 
            trend="1 in progress"
            trendUp={true}
          />
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Actions */}
            <Card className="p-6 shadow-card">
              <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {quickActions.map((action, index) => (
                  <Link key={index} to={action.path}>
                    <button className="w-full p-4 rounded-lg border hover:shadow-md transition-shadow text-center">
                      <div className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center mx-auto mb-2`}>
                        <action.icon size={24} />
                      </div>
                      <p className="text-sm font-medium">{action.label}</p>
                    </button>
                  </Link>
                ))}
              </div>
            </Card>

            {/* Learning Progress */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Continue Learning</h2>
                <Link to="/learning" className="text-sm text-primary hover:underline">View All</Link>
              </div>
              <div className="space-y-4">
                {upcomingCourses.map((course, index) => (
                  <div key={index} className="p-4 border rounded-lg hover:border-primary/50 transition-colors">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-medium mb-1">{course.title}</h3>
                        <p className="text-sm text-muted-foreground">Next: {course.nextLesson}</p>
                      </div>
                      <span className="text-sm font-semibold text-primary">{course.progress}%</span>
                    </div>
                    <Progress value={course.progress} className="h-2" />
                  </div>
                ))}
              </div>
            </Card>

            {/* Matched Jobs */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Top Job Matches</h2>
                <Link to="/jobs" className="text-sm text-primary hover:underline">View All</Link>
              </div>
              <div className="space-y-3">
                {matchedJobs.map((job, index) => (
                  <div key={index} className="p-4 border rounded-lg hover:border-secondary/50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-medium mb-1">{job.title}</h3>
                        <p className="text-sm text-muted-foreground">{job.company} • {job.location}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-secondary">{job.match}%</div>
                        <div className="text-xs text-muted-foreground">Match</div>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" className="w-full mt-2">
                      View Details <ArrowRight size={14} className="ml-2" />
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* AI Assistant */}
            <Card className="p-6 shadow-card bg-gradient-primary text-primary-foreground">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-primary-foreground/20 rounded-full flex items-center justify-center">
                  <MessageCircle size={20} />
                </div>
                <h3 className="font-semibold">AI Career Assistant</h3>
              </div>
              <p className="text-sm mb-4 text-primary-foreground/90">
                Get personalized recommendations and career advice
              </p>
              <Button variant="accent" className="w-full">
                Start Chat
              </Button>
            </Card>

            {/* Learning Calendar */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center gap-2 mb-4">
                <Calendar className="text-primary" size={20} />
                <h3 className="font-semibold">Upcoming Sessions</h3>
              </div>
              <div className="space-y-3">
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-1">React Workshop</p>
                  <p className="text-xs text-muted-foreground">Today, 3:00 PM</p>
                </div>
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-1">Career Counseling</p>
                  <p className="text-xs text-muted-foreground">Tomorrow, 10:00 AM</p>
                </div>
              </div>
            </Card>

            {/* Market Insights */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="text-accent" size={20} />
                <h3 className="font-semibold">Market Insights</h3>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">React Demand</span>
                    <span className="font-semibold text-secondary">↑ High</span>
                  </div>
                  <Progress value={85} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Python Demand</span>
                    <span className="font-semibold text-secondary">↑ High</span>
                  </div>
                  <Progress value={90} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Cloud Skills</span>
                    <span className="font-semibold text-accent">↑ Growing</span>
                  </div>
                  <Progress value={75} className="h-2" />
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
