import Navigation from "@/components/Navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  User, 
  Briefcase, 
  Award, 
  FileText, 
  CreditCard,
  Edit,
  Upload,
  ExternalLink,
  Plus,
  Trash2
} from "lucide-react";

const Profile = () => {
  const profileStrength = 85;

  const skills = [
    { name: "React", level: 85, verified: true },
    { name: "TypeScript", level: 78, verified: true },
    { name: "Node.js", level: 72, verified: false },
    { name: "Python", level: 68, verified: false },
  ];

  const certifications = [
    {
      title: "AWS Certified Solutions Architect",
      issuer: "Amazon Web Services",
      date: "Dec 2024",
      verified: true
    },
    {
      title: "React Professional Certificate",
      issuer: "Meta",
      date: "Nov 2024",
      verified: true
    },
    {
      title: "Advanced JavaScript",
      issuer: "Udemy",
      date: "Oct 2024",
      verified: false
    },
  ];

  const portfolio = [
    {
      title: "E-commerce Platform",
      description: "Full-stack e-commerce solution built with React and Node.js",
      tech: ["React", "Node.js", "MongoDB"],
      link: "github.com/project1"
    },
    {
      title: "Task Management App",
      description: "Real-time collaboration tool with WebSocket integration",
      tech: ["React", "TypeScript", "Firebase"],
      link: "github.com/project2"
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Profile & Settings</h1>
          <p className="text-muted-foreground">Manage your account and preferences</p>
        </div>

        {/* Profile Strength Card */}
        <Card className="p-6 shadow-card mb-6 bg-gradient-primary text-primary-foreground">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-lg mb-1">Profile Strength</h3>
              <p className="text-sm text-primary-foreground/90">Complete your profile to unlock all features</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">{profileStrength}%</div>
            </div>
          </div>
          <Progress value={profileStrength} className="h-2 bg-primary-foreground/20" />
        </Card>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Profile Picture & Quick Info */}
          <div className="lg:col-span-1 space-y-6">
            <Card className="p-6 shadow-card text-center">
              <div className="w-24 h-24 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="text-primary-foreground" size={48} />
              </div>
              <h2 className="text-xl font-bold mb-1">Ahmed Mohamed</h2>
              <p className="text-muted-foreground mb-4">Frontend Developer</p>
              <Button variant="outline" className="w-full mb-2">
                <Upload size={16} />
                Change Photo
              </Button>
              <Button variant="ghost" className="w-full">
                <ExternalLink size={16} />
                View Public Profile
              </Button>
            </Card>

            <Card className="p-6 shadow-card">
              <h3 className="font-semibold mb-4">Quick Stats</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Courses Completed</span>
                  <span className="font-semibold">12</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Certifications</span>
                  <span className="font-semibold">5</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Profile Views</span>
                  <span className="font-semibold">234</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Member Since</span>
                  <span className="font-semibold">Jan 2024</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Content Tabs */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="personal" className="space-y-6">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="personal">Personal</TabsTrigger>
                <TabsTrigger value="skills">Skills</TabsTrigger>
                <TabsTrigger value="certs">Certificates</TabsTrigger>
                <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
                <TabsTrigger value="billing">Billing</TabsTrigger>
              </TabsList>

              {/* Personal Info */}
              <TabsContent value="personal">
                <Card className="p-6 shadow-card">
                  <h3 className="font-semibold text-lg mb-4">Personal Information</h3>
                  <div className="space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">First Name</Label>
                        <Input id="firstName" defaultValue="Ahmed" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Last Name</Label>
                        <Input id="lastName" defaultValue="Mohamed" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input id="email" type="email" defaultValue="ahmed@example.com" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone</Label>
                      <Input id="phone" defaultValue="+20 123 456 7890" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="bio">Bio</Label>
                      <Textarea 
                        id="bio" 
                        defaultValue="Passionate frontend developer with 5+ years of experience building modern web applications."
                        rows={4}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="location">Location</Label>
                      <Input id="location" defaultValue="Cairo, Egypt" />
                    </div>
                    <Button variant="hero">Save Changes</Button>
                  </div>
                </Card>
              </TabsContent>

              {/* Skills */}
              <TabsContent value="skills">
                <Card className="p-6 shadow-card">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-lg">Your Skills</h3>
                    <Button variant="outline" size="sm">
                      <Plus size={16} />
                      Add Skill
                    </Button>
                  </div>
                  <div className="space-y-4">
                    {skills.map((skill, index) => (
                      <div key={index} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{skill.name}</span>
                            {skill.verified && (
                              <Badge variant="secondary" className="text-xs">Verified</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-primary">{skill.level}%</span>
                            <Button variant="ghost" size="sm">
                              <Edit size={14} />
                            </Button>
                          </div>
                        </div>
                        <Progress value={skill.level} className="h-2" />
                      </div>
                    ))}
                  </div>
                </Card>
              </TabsContent>

              {/* Certifications */}
              <TabsContent value="certs">
                <Card className="p-6 shadow-card">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-lg">Certifications</h3>
                    <Button variant="outline" size="sm">
                      <Plus size={16} />
                      Add Certificate
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {certifications.map((cert, index) => (
                      <div key={index} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between">
                          <div className="flex gap-3">
                            <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                              <Award className="text-secondary" size={24} />
                            </div>
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-semibold">{cert.title}</h4>
                                {cert.verified && (
                                  <Badge variant="secondary" className="text-xs">Verified</Badge>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground">{cert.issuer}</p>
                              <p className="text-xs text-muted-foreground mt-1">{cert.date}</p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm">
                            <Trash2 size={14} />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </TabsContent>

              {/* Portfolio */}
              <TabsContent value="portfolio">
                <Card className="p-6 shadow-card">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-lg">Portfolio Projects</h3>
                    <Button variant="outline" size="sm">
                      <Plus size={16} />
                      Add Project
                    </Button>
                  </div>
                  <div className="space-y-4">
                    {portfolio.map((project, index) => (
                      <div key={index} className="p-4 border rounded-lg">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-semibold mb-1">{project.title}</h4>
                            <p className="text-sm text-muted-foreground mb-3">{project.description}</p>
                            <div className="flex flex-wrap gap-2">
                              {project.tech.map((tech, i) => (
                                <Badge key={i} variant="secondary">{tech}</Badge>
                              ))}
                            </div>
                          </div>
                          <Button variant="ghost" size="sm">
                            <Edit size={14} />
                          </Button>
                        </div>
                        <a href="#" className="text-sm text-primary hover:underline flex items-center gap-1">
                          {project.link}
                          <ExternalLink size={12} />
                        </a>
                      </div>
                    ))}
                  </div>
                </Card>
              </TabsContent>

              {/* Billing */}
              <TabsContent value="billing">
                <Card className="p-6 shadow-card">
                  <h3 className="font-semibold text-lg mb-4">Subscription & Billing</h3>
                  <div className="space-y-6">
                    <div className="p-4 border rounded-lg bg-muted/30">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">Current Plan</span>
                        <Badge>Free</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-4">
                        Upgrade to unlock premium features and get unlimited access
                      </p>
                      <Button variant="accent">Upgrade to Pro</Button>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3">Payment Method</h4>
                      <Button variant="outline">
                        <CreditCard size={16} />
                        Add Payment Method
                      </Button>
                    </div>
                  </div>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
