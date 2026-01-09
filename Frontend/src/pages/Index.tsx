import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Target, MapIcon, MessageSquare, TrendingUp, Users, Award, ArrowRight, Sparkles } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <nav className="flex items-center justify-between mb-16">
          <div className="flex items-center space-x-2">
            <div className="h-10 w-10 rounded-xl gradient-primary flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-xl">S</span>
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Sha8alny
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link to="/register">
              <Button className="gradient-primary">Get Started</Button>
            </Link>
          </div>
        </nav>

        <div className="text-center max-w-4xl mx-auto mb-16">
          <Badge className="mb-4 bg-primary/10 text-primary border-primary">
            <Sparkles className="h-3 w-3 mr-1" />
            AI-Powered Career Development
          </Badge>
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Transform Your
            <span className="bg-gradient-to-r from-primary via-primary to-accent bg-clip-text text-transparent">
              {" "}Career Journey{" "}
            </span>
            with AI
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Get personalized skill assessments, learning roadmaps, and career guidance powered by
            artificial intelligence. Your path to professional growth starts here.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg" className="gradient-primary text-lg px-8">
                Start Your Journey
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="text-lg px-8">
                Sign In
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <Card className="transition-smooth hover:shadow-xl">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg gradient-primary flex items-center justify-center mb-4">
                <Target className="h-6 w-6 text-primary-foreground" />
              </div>
              <CardTitle>AI Skill Assessment</CardTitle>
              <CardDescription>
                Take comprehensive assessments tailored to your target career path and get detailed
                insights on your strengths and gaps
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="transition-smooth hover:shadow-xl">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg gradient-primary flex items-center justify-center mb-4">
                <MapIcon className="h-6 w-6 text-primary-foreground" />
              </div>
              <CardTitle>Learning Roadmaps</CardTitle>
              <CardDescription>
                Get personalized learning paths with milestones, resources, and timelines designed
                to help you reach your career goals faster
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="transition-smooth hover:shadow-xl">
            <CardHeader>
              <div className="h-12 w-12 rounded-lg gradient-primary flex items-center justify-center mb-4">
                <MessageSquare className="h-6 w-6 text-primary-foreground" />
              </div>
              <CardTitle>Career Advisor</CardTitle>
              <CardDescription>
                Chat with our AI career advisor for personalized guidance, answers to your
                questions, and strategic career advice
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Stats Section */}
        <Card className="gradient-accent text-accent-foreground mb-16">
          <CardContent className="py-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div>
                <div className="text-5xl font-bold mb-2 flex items-center justify-center gap-2">
                  <Users className="h-10 w-10" />
                  10K+
                </div>
                <p className="text-lg opacity-90">Active Learners</p>
              </div>
              <div>
                <div className="text-5xl font-bold mb-2 flex items-center justify-center gap-2">
                  <Target className="h-10 w-10" />
                  500+
                </div>
                <p className="text-lg opacity-90">Career Paths</p>
              </div>
              <div>
                <div className="text-5xl font-bold mb-2 flex items-center justify-center gap-2">
                  <Award className="h-10 w-10" />
                  95%
                </div>
                <p className="text-lg opacity-90">Success Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* How It Works */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          <h2 className="text-4xl font-bold mb-12">How Sha8alny Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <span className="text-3xl font-bold text-primary">1</span>
              </div>
              <h3 className="text-xl font-semibold">Take Assessment</h3>
              <p className="text-muted-foreground">
                Complete an AI-powered assessment to identify your skills, strengths, and areas for
                improvement
              </p>
            </div>
            <div className="space-y-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <span className="text-3xl font-bold text-primary">2</span>
              </div>
              <h3 className="text-xl font-semibold">Get Roadmap</h3>
              <p className="text-muted-foreground">
                Receive a personalized learning roadmap with milestones, resources, and timelines
              </p>
            </div>
            <div className="space-y-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <span className="text-3xl font-bold text-primary">3</span>
              </div>
              <h3 className="text-xl font-semibold">Track Progress</h3>
              <p className="text-muted-foreground">
                Monitor your progress, earn achievements, and get continuous AI guidance
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <Card className="gradient-primary text-primary-foreground">
          <CardContent className="py-12 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Career?</h2>
            <p className="text-lg mb-8 opacity-90 max-w-2xl mx-auto">
              Join thousands of professionals who are already accelerating their career growth with
              Sha8alny
            </p>
            <Link to="/register">
              <Button size="lg" variant="secondary" className="text-lg px-8">
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>&copy; 2025 Sha8alny. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
