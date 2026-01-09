import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Target, Clock, FileText, Search, TrendingUp } from "lucide-react";

export default function Assessment() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");

  const careerPaths = [
    {
      title: "Software Engineer",
      description: "Build and maintain software applications",
      questions: 25,
      duration: "30-45 min",
      difficulty: "Intermediate",
      popular: true,
    },
    {
      title: "Data Scientist",
      description: "Analyze data and build predictive models",
      questions: 28,
      duration: "40-50 min",
      difficulty: "Advanced",
      popular: true,
    },
    {
      title: "Product Manager",
      description: "Lead cross-functional teams to build products",
      questions: 20,
      duration: "25-35 min",
      difficulty: "Intermediate",
      popular: false,
    },
    {
      title: "Frontend Developer",
      description: "Create engaging user interfaces with modern frameworks",
      questions: 22,
      duration: "30-40 min",
      difficulty: "Intermediate",
      popular: true,
    },
    {
      title: "Backend Developer",
      description: "Design and build scalable APIs and services",
      questions: 24,
      duration: "35-45 min",
      difficulty: "Advanced",
      popular: false,
    },
    {
      title: "DevOps Engineer",
      description: "Automate infrastructure and improve delivery pipelines",
      questions: 26,
      duration: "40-50 min",
      difficulty: "Advanced",
      popular: false,
    },
    {
      title: "Machine Learning Engineer",
      description: "Build and deploy machine learning models",
      questions: 30,
      duration: "45-60 min",
      difficulty: "Advanced",
      popular: true,
    },
    {
      title: "UI/UX Designer",
      description: "Design intuitive and user-friendly experiences",
      questions: 18,
      duration: "25-35 min",
      difficulty: "Intermediate",
      popular: false,
    },
    {
      title: "Full Stack Developer",
      description: "Work on both frontend and backend",
      questions: 30,
      duration: "45-60 min",
      difficulty: "Intermediate",
      popular: true,
    },
  ];

  const filteredPaths = careerPaths.filter(
    (path) =>
      path.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      path.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl gradient-primary mb-4">
          <Target className="h-8 w-8 text-primary-foreground" />
        </div>
        <h1 className="text-4xl font-bold">AI Skill Assessment</h1>
        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          Take a comprehensive skills assessment tailored to your target career path. Get personalized
          insights and recommendations based on your responses.
        </p>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">How it works</CardTitle>
            <CardDescription>Three simple steps to get your personalized roadmap</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-primary font-bold">1</span>
              </div>
              <div>
                <h4 className="font-semibold mb-1">Choose a Path</h4>
                <p className="text-sm text-muted-foreground">
                  Select a career path that interests you or enter a custom role
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-primary font-bold">2</span>
              </div>
              <div>
                <h4 className="font-semibold mb-1">Complete Assessment</h4>
                <p className="text-sm text-muted-foreground">
                  Answer questions at your own pace with various question types
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-primary font-bold">3</span>
              </div>
              <div>
                <h4 className="font-semibold mb-1">Get Results</h4>
                <p className="text-sm text-muted-foreground">
                  Review your strengths, gaps, and generate a learning roadmap
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Question Types</CardTitle>
            <CardDescription>A mix of formats to capture your skills accurately</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <ul className="space-y-2 list-disc list-inside">
              <li>Multiple-choice questions to assess core knowledge</li>
              <li>Rating scales to understand your confidence levels</li>
              <li>Scenario-based and open questions for deeper insight</li>
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">What you get</CardTitle>
            <CardDescription>Actionable outcomes from your assessment</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <ul className="space-y-2 list-disc list-inside">
              <li>Overall readiness level for your chosen path</li>
              <li>Breakdown of strengths and skill gaps</li>
              <li>Personalized learning roadmap recommendations</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Search & Custom Path */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Select a Career Path</span>
            <Badge variant="outline" className="text-xs">
              <TrendingUp className="h-3 w-3 mr-1" />
              Popular choices highlighted
            </Badge>
          </CardTitle>
          <CardDescription>
            Choose from common tech careers or use the search to find what matches your goals.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search career paths..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button
              variant="outline"
              type="button"
              onClick={() => navigate("/assessment/session?path=Custom%20Career%20Path")}
            >
              <FileText className="mr-2 h-4 w-4" />
              Custom Career Path
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Career Paths Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredPaths.map((path) => (
          <Card
            key={path.title}
            className="transition-smooth hover:shadow-lg cursor-pointer group"
            onClick={() => navigate(`/assessment/session?path=${encodeURIComponent(path.title)}`)}
          >
            <CardHeader>
              <div className="flex items-start justify-between mb-2">
                <CardTitle className="text-xl group-hover:text-primary transition-smooth">
                  {path.title}
                </CardTitle>
                {path.popular && (
                  <Badge variant="secondary" className="bg-accent/10 text-accent">
                    <TrendingUp className="h-3 w-3 mr-1" />
                    Popular
                  </Badge>
                )}
              </div>
              <CardDescription>{path.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center text-muted-foreground">
                  <FileText className="h-4 w-4 mr-2" />
                  {path.questions} questions
                </div>
                <div className="flex items-center text-muted-foreground">
                  <Clock className="h-4 w-4 mr-2" />
                  {path.duration}
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Difficulty: {path.difficulty}</span>
                <span>AI-powered assessment</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredPaths.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No career paths found matching your search.</p>
          <Button variant="outline" className="mt-4" onClick={() => setSearchQuery("")}>
            Clear Search
          </Button>
        </div>
      )}
    </div>
  );
}
