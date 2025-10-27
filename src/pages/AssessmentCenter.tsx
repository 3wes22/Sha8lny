import Navigation from "@/components/Navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Target, 
  Brain, 
  Code, 
  Zap, 
  Trophy,
  Clock,
  CheckCircle,
  PlayCircle,
  BarChart3
} from "lucide-react";

const AssessmentCenter = () => {
  const assessmentTypes = [
    {
      icon: Code,
      title: "Technical Skills",
      description: "Evaluate your programming and technical knowledge",
      duration: "45 min",
      questions: 30,
      difficulty: "Adaptive",
      color: "bg-primary/10 text-primary"
    },
    {
      icon: Brain,
      title: "Cognitive Abilities",
      description: "Test your problem-solving and logical thinking",
      duration: "30 min",
      questions: 25,
      difficulty: "Progressive",
      color: "bg-secondary/10 text-secondary"
    },
    {
      icon: Zap,
      title: "Soft Skills",
      description: "Assess communication and teamwork capabilities",
      duration: "20 min",
      questions: 20,
      difficulty: "Scenario-based",
      color: "bg-accent/10 text-accent"
    },
    {
      icon: Target,
      title: "Career Readiness",
      description: "Comprehensive evaluation of job market preparedness",
      duration: "60 min",
      questions: 40,
      difficulty: "Comprehensive",
      color: "bg-purple-100 text-purple-600"
    },
  ];

  const completedAssessments = [
    {
      title: "Full Stack Development",
      score: 85,
      date: "Jan 15, 2025",
      percentile: 92,
      status: "Excellent"
    },
    {
      title: "JavaScript Fundamentals",
      score: 78,
      date: "Jan 10, 2025",
      percentile: 85,
      status: "Good"
    },
    {
      title: "Problem Solving",
      score: 90,
      date: "Jan 5, 2025",
      percentile: 95,
      status: "Outstanding"
    },
  ];

  const skillBreakdown = [
    { skill: "React", level: 85, category: "Expert" },
    { skill: "JavaScript", level: 78, category: "Advanced" },
    { skill: "TypeScript", level: 72, category: "Advanced" },
    { skill: "Node.js", level: 68, category: "Intermediate" },
    { skill: "Python", level: 65, category: "Intermediate" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Assessment Center</h1>
          <p className="text-muted-foreground">Evaluate your skills and get personalized insights</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4 shadow-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                <Trophy className="text-primary" size={20} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold">12</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 shadow-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-secondary/10 rounded-lg flex items-center justify-center">
                <Target className="text-secondary" size={20} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Avg Score</p>
                <p className="text-2xl font-bold">84%</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 shadow-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                <BarChart3 className="text-accent" size={20} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Percentile</p>
                <p className="text-2xl font-bold">89th</p>
              </div>
            </div>
          </Card>
          <Card className="p-4 shadow-card">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="text-purple-600" size={20} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Skills Verified</p>
                <p className="text-2xl font-bold">15</p>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Available Assessments */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Available Assessments</h2>
              <div className="grid md:grid-cols-2 gap-4">
                {assessmentTypes.map((assessment, index) => (
                  <Card key={index} className="p-6 shadow-card hover:shadow-lg transition-shadow">
                    <div className={`w-12 h-12 ${assessment.color} rounded-lg flex items-center justify-center mb-4`}>
                      <assessment.icon size={24} />
                    </div>
                    <h3 className="font-semibold text-lg mb-2">{assessment.title}</h3>
                    <p className="text-sm text-muted-foreground mb-4">{assessment.description}</p>
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Duration</span>
                        <span className="font-medium">{assessment.duration}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Questions</span>
                        <span className="font-medium">{assessment.questions}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Difficulty</span>
                        <Badge variant="secondary">{assessment.difficulty}</Badge>
                      </div>
                    </div>
                    <Button variant="hero" className="w-full">
                      <PlayCircle size={16} />
                      Start Assessment
                    </Button>
                  </Card>
                ))}
              </div>
            </div>

            {/* Recent Results */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Recent Results</h2>
              <div className="space-y-3">
                {completedAssessments.map((assessment, index) => (
                  <Card key={index} className="p-6 shadow-card">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-semibold mb-1">{assessment.title}</h3>
                        <p className="text-sm text-muted-foreground">{assessment.date}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-secondary">{assessment.score}%</div>
                        <Badge 
                          variant={assessment.score >= 85 ? "default" : "secondary"}
                          className="mt-1"
                        >
                          {assessment.status}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">Your Score</span>
                      <span className="text-sm font-medium">{assessment.percentile}th percentile</span>
                    </div>
                    <Progress value={assessment.score} className="h-2 mb-3" />
                    <Button variant="outline" size="sm" className="w-full">
                      View Detailed Report
                    </Button>
                  </Card>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Skill Breakdown */}
            <Card className="p-6 shadow-card">
              <h3 className="font-semibold mb-4">Your Skill Profile</h3>
              <div className="space-y-4">
                {skillBreakdown.map((skill, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{skill.skill}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-primary">{skill.level}%</span>
                        <Badge variant="secondary" className="text-xs">{skill.category}</Badge>
                      </div>
                    </div>
                    <Progress value={skill.level} className="h-2" />
                  </div>
                ))}
              </div>
            </Card>

            {/* Recommendations */}
            <Card className="p-6 shadow-card bg-gradient-primary text-primary-foreground">
              <h3 className="font-semibold mb-3">Next Steps</h3>
              <p className="text-sm mb-4 text-primary-foreground/90">
                Take the Career Readiness assessment to get personalized job recommendations
              </p>
              <Button variant="accent" className="w-full">
                Start Now
              </Button>
            </Card>

            {/* Tips */}
            <Card className="p-6 shadow-card">
              <h3 className="font-semibold mb-3">Assessment Tips</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-secondary mt-0.5 flex-shrink-0" />
                  <span>Find a quiet environment</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-secondary mt-0.5 flex-shrink-0" />
                  <span>Ensure stable internet connection</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-secondary mt-0.5 flex-shrink-0" />
                  <span>Read questions carefully</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle size={16} className="text-secondary mt-0.5 flex-shrink-0" />
                  <span>Manage your time wisely</span>
                </li>
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentCenter;
