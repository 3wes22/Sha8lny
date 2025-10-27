import Navigation from "@/components/Navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { BookOpen, PlayCircle, Award, Calendar, Clock, TrendingUp, Sparkles } from "lucide-react";

const LearningHub = () => {
  const myCourses = [
    { 
      title: "Advanced React Development", 
      progress: 65, 
      totalLessons: 24, 
      completedLessons: 16,
      nextLesson: "Custom Hooks Deep Dive",
      duration: "12 hours",
      instructor: "Sarah Ahmed"
    },
    { 
      title: "Python for Data Science", 
      progress: 40, 
      totalLessons: 30, 
      completedLessons: 12,
      nextLesson: "Working with Pandas",
      duration: "18 hours",
      instructor: "Mohamed Hassan"
    },
    { 
      title: "AWS Cloud Architecture", 
      progress: 20, 
      totalLessons: 20, 
      completedLessons: 4,
      nextLesson: "EC2 Fundamentals",
      duration: "15 hours",
      instructor: "Ahmed Khaled"
    },
  ];

  const recommendedCourses = [
    {
      title: "TypeScript Masterclass",
      level: "Intermediate",
      duration: "10 hours",
      rating: 4.8,
      students: "15K+",
      aiScore: 95
    },
    {
      title: "Node.js Backend Development",
      level: "Advanced",
      duration: "14 hours",
      rating: 4.9,
      students: "20K+",
      aiScore: 92
    },
    {
      title: "Docker & Kubernetes",
      level: "Intermediate",
      duration: "12 hours",
      rating: 4.7,
      students: "18K+",
      aiScore: 88
    },
    {
      title: "System Design Interview Prep",
      level: "Advanced",
      duration: "16 hours",
      rating: 4.9,
      students: "25K+",
      aiScore: 90
    },
  ];

  const learningPaths = [
    {
      title: "Full Stack Web Developer",
      courses: 8,
      duration: "6 months",
      level: "Beginner to Advanced",
      completion: 35
    },
    {
      title: "Data Science Professional",
      courses: 10,
      duration: "8 months",
      level: "Intermediate",
      completion: 15
    },
    {
      title: "Cloud Solutions Architect",
      courses: 6,
      duration: "4 months",
      level: "Intermediate",
      completion: 10
    },
  ];

  const achievements = [
    { icon: "🏆", title: "5 Day Streak", description: "Keep it up!" },
    { icon: "⭐", title: "Fast Learner", description: "Completed 3 courses this month" },
    { icon: "🎯", title: "Goal Achiever", description: "Hit your learning targets" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Learning Hub</h1>
          <p className="text-muted-foreground">Your personalized learning journey</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="courses" className="space-y-6">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="courses">My Courses</TabsTrigger>
                <TabsTrigger value="paths">Learning Paths</TabsTrigger>
                <TabsTrigger value="projects">Projects</TabsTrigger>
                <TabsTrigger value="certificates">Certificates</TabsTrigger>
              </TabsList>

              {/* My Courses Tab */}
              <TabsContent value="courses" className="space-y-4">
                {myCourses.map((course, index) => (
                  <Card key={index} className="p-6 shadow-card">
                    <div className="flex flex-col md:flex-row gap-4">
                      <div className="w-full md:w-24 h-24 bg-gradient-primary rounded-lg flex items-center justify-center flex-shrink-0">
                        <BookOpen className="text-primary-foreground" size={32} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="font-semibold text-lg mb-1">{course.title}</h3>
                            <p className="text-sm text-muted-foreground">By {course.instructor}</p>
                          </div>
                          <span className="text-sm font-semibold text-primary">{course.progress}%</span>
                        </div>
                        <Progress value={course.progress} className="h-2 mb-3" />
                        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-3">
                          <span>{course.completedLessons}/{course.totalLessons} lessons</span>
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {course.duration}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <Button variant="hero">
                            <PlayCircle size={16} />
                            Continue: {course.nextLesson}
                          </Button>
                          <Button variant="outline">View Details</Button>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </TabsContent>

              {/* Learning Paths Tab */}
              <TabsContent value="paths" className="space-y-4">
                {learningPaths.map((path, index) => (
                  <Card key={index} className="p-6 shadow-card">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-semibold text-lg mb-2">{path.title}</h3>
                        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                          <span>{path.courses} courses</span>
                          <span>{path.duration}</span>
                          <span>{path.level}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-secondary">{path.completion}%</div>
                        <div className="text-xs text-muted-foreground">Complete</div>
                      </div>
                    </div>
                    <Progress value={path.completion} className="h-2 mb-4" />
                    <Button variant="secondary" className="w-full">Continue Path</Button>
                  </Card>
                ))}
              </TabsContent>

              {/* Projects Tab */}
              <TabsContent value="projects">
                <Card className="p-6 shadow-card text-center">
                  <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <TrendingUp className="text-accent" size={32} />
                  </div>
                  <h3 className="font-semibold text-xl mb-2">Build Real Projects</h3>
                  <p className="text-muted-foreground mb-6">
                    Apply your skills with hands-on projects and build your portfolio
                  </p>
                  <Button variant="accent">Browse Projects</Button>
                </Card>
              </TabsContent>

              {/* Certificates Tab */}
              <TabsContent value="certificates">
                <Card className="p-6 shadow-card text-center">
                  <div className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Award className="text-secondary" size={32} />
                  </div>
                  <h3 className="font-semibold text-xl mb-2">Your Certifications</h3>
                  <p className="text-muted-foreground mb-6">
                    Complete courses to earn industry-recognized certificates
                  </p>
                  <Button variant="secondary">View All Certificates</Button>
                </Card>
              </TabsContent>
            </Tabs>

            {/* AI Recommended Courses */}
            <div className="mt-8">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="text-accent" size={20} />
                <h2 className="text-xl font-semibold">AI Recommended for You</h2>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                {recommendedCourses.map((course, index) => (
                  <Card key={index} className="p-4 shadow-card hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold mb-2">{course.title}</h3>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                          <span className="px-2 py-1 bg-muted rounded">{course.level}</span>
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            {course.duration}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-accent">★ {course.rating}</span>
                          <span className="text-muted-foreground">• {course.students} students</span>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-secondary">{course.aiScore}%</div>
                        <div className="text-xs text-muted-foreground">Match</div>
                      </div>
                    </div>
                    <Button variant="outline" className="w-full" size="sm">Enroll Now</Button>
                  </Card>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Learning Calendar */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center gap-2 mb-4">
                <Calendar className="text-primary" size={20} />
                <h3 className="font-semibold">This Week's Schedule</h3>
              </div>
              <div className="space-y-3">
                {["Monday", "Wednesday", "Friday"].map((day, i) => (
                  <div key={i} className="p-3 bg-muted rounded-lg">
                    <p className="text-sm font-medium mb-1">{day}</p>
                    <p className="text-xs text-muted-foreground">2 hours • React Course</p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Achievements */}
            <Card className="p-6 shadow-card">
              <h3 className="font-semibold mb-4">Recent Achievements</h3>
              <div className="space-y-3">
                {achievements.map((achievement, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-muted rounded-lg">
                    <span className="text-2xl">{achievement.icon}</span>
                    <div>
                      <p className="font-medium text-sm">{achievement.title}</p>
                      <p className="text-xs text-muted-foreground">{achievement.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Progress Stats */}
            <Card className="p-6 shadow-card">
              <h3 className="font-semibold mb-4">Your Progress</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Weekly Goal</span>
                    <span className="font-semibold">8/10 hours</span>
                  </div>
                  <Progress value={80} className="h-2" />
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Lessons This Month</span>
                    <span className="font-semibold">32 completed</span>
                  </div>
                  <Progress value={65} className="h-2" />
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningHub;
