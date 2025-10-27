import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { 
  Target, 
  BookOpen, 
  Briefcase, 
  TrendingUp, 
  Users, 
  Award,
  CheckCircle,
  Sparkles,
  BarChart3,
  Globe
} from "lucide-react";

const Landing = () => {
  const stats = [
    { value: "50K+", label: "Active Users" },
    { value: "1000+", label: "Available Jobs" },
    { value: "500+", label: "Learning Paths" },
    { value: "95%", label: "Success Rate" },
  ];

  const features = [
    {
      icon: Target,
      title: "AI-Powered Assessment",
      description: "Comprehensive skill evaluation using advanced AI algorithms tailored for the Egyptian market."
    },
    {
      icon: BookOpen,
      title: "Personalized Learning",
      description: "Custom learning paths designed specifically for your career goals and skill gaps."
    },
    {
      icon: Briefcase,
      title: "Job Matching",
      description: "Smart job recommendations based on your skills, preferences, and career aspirations."
    },
    {
      icon: TrendingUp,
      title: "Career Growth",
      description: "Track your progress and receive insights to accelerate your professional development."
    },
    {
      icon: Users,
      title: "Corporate Solutions",
      description: "Enterprise-grade tools for organizations to upskill their workforce effectively."
    },
    {
      icon: Award,
      title: "Certified Programs",
      description: "Industry-recognized certifications to validate your skills and boost your career."
    }
  ];

  const steps = [
    {
      number: "01",
      title: "Assess Your Skills",
      description: "Take our comprehensive AI-powered assessment to understand your current capabilities."
    },
    {
      number: "02",
      title: "Get Your Learning Path",
      description: "Receive a personalized learning roadmap designed to fill your skill gaps."
    },
    {
      number: "03",
      title: "Land Your Dream Job",
      description: "Apply to matched job opportunities and advance your career with confidence."
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-hero py-20 md:py-32">
        <div className="absolute inset-0 bg-grid-white/10" />
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl mx-auto text-center space-y-8">
            <div className="inline-flex items-center gap-2 bg-primary-foreground/10 backdrop-blur-sm px-4 py-2 rounded-full text-primary-foreground">
              <Sparkles size={16} />
              <span className="text-sm font-medium">AI-Powered Career Development</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-primary-foreground">
              Transform Your Career with{" "}
              <span className="text-accent">SkillPath AI</span>
            </h1>
            <p className="text-xl text-primary-foreground/90 max-w-2xl mx-auto">
              Discover your potential, learn smarter, and get hired faster with Egypt's leading AI-driven career development platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="accent" asChild className="text-lg px-8">
                <Link to="/register">Start Free Assessment</Link>
              </Button>
              <Button size="lg" variant="outline" asChild className="text-lg px-8 bg-primary-foreground/10 border-primary-foreground/20 text-primary-foreground hover:bg-primary-foreground/20">
                <Link to="/demo">Watch Demo</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Market Intelligence Widget */}
      <section className="py-12 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-primary mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Your journey to career success in three simple steps
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {steps.map((step, index) => (
              <Card key={index} className="p-8 text-center shadow-card hover:shadow-lg transition-shadow">
                <div className="w-16 h-16 bg-gradient-primary rounded-full flex items-center justify-center text-3xl font-bold text-primary-foreground mx-auto mb-6">
                  {step.number}
                </div>
                <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                <p className="text-muted-foreground">{step.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Powerful Features</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Everything you need to succeed in your career journey
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 shadow-card hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="text-secondary" size={24} />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground text-sm">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Success Stories</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Hear from professionals who transformed their careers
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-6 shadow-card">
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(5)].map((_, j) => (
                    <span key={j} className="text-accent">★</span>
                  ))}
                </div>
                <p className="text-muted-foreground mb-4">
                  "SkillPath AI helped me identify my skill gaps and provided a clear path to my dream job. The personalized learning recommendations were spot-on!"
                </p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-primary rounded-full" />
                  <div>
                    <div className="font-semibold">User {i}</div>
                    <div className="text-sm text-muted-foreground">Software Engineer</div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-hero">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-primary-foreground mb-4">
            Ready to Start Your Journey?
          </h2>
          <p className="text-xl text-primary-foreground/90 mb-8 max-w-2xl mx-auto">
            Join thousands of professionals advancing their careers with SkillPath AI
          </p>
          <Button size="lg" variant="accent" asChild className="text-lg px-8">
            <Link to="/register">Get Started Free</Link>
          </Button>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;
