import Navigation from "@/components/Navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Search, 
  MapPin, 
  Briefcase, 
  Clock, 
  DollarSign, 
  Building,
  Heart,
  ExternalLink,
  TrendingUp,
  Filter
} from "lucide-react";

const JobMarketplace = () => {
  const jobs = [
    {
      title: "Senior React Developer",
      company: "Tech Innovators",
      location: "Cairo, Egypt",
      type: "Full-time",
      salary: "EGP 25,000 - 35,000",
      match: 95,
      posted: "2 days ago",
      skills: ["React", "TypeScript", "Node.js"],
      applicants: 23
    },
    {
      title: "Full Stack Engineer",
      company: "Digital Solutions",
      location: "Remote",
      type: "Full-time",
      salary: "EGP 30,000 - 45,000",
      match: 92,
      posted: "1 day ago",
      skills: ["React", "Python", "AWS"],
      applicants: 15
    },
    {
      title: "Frontend Developer",
      company: "Creative Agency",
      location: "Alexandria, Egypt",
      type: "Full-time",
      salary: "EGP 20,000 - 28,000",
      match: 88,
      posted: "3 days ago",
      skills: ["React", "CSS", "JavaScript"],
      applicants: 31
    },
    {
      title: "React Native Developer",
      company: "Mobile First",
      location: "Cairo, Egypt",
      type: "Contract",
      salary: "EGP 35,000 - 50,000",
      match: 85,
      posted: "5 days ago",
      skills: ["React Native", "TypeScript", "Firebase"],
      applicants: 18
    },
  ];

  const applicationPipeline = [
    { stage: "Applied", count: 5, color: "bg-blue-500" },
    { stage: "Screening", count: 3, color: "bg-yellow-500" },
    { stage: "Interview", count: 2, color: "bg-orange-500" },
    { stage: "Offer", count: 1, color: "bg-green-500" },
  ];

  const marketInsights = [
    { skill: "React", demand: "Very High", trend: "+15%", color: "text-secondary" },
    { skill: "TypeScript", demand: "High", trend: "+22%", color: "text-secondary" },
    { skill: "Python", demand: "High", trend: "+18%", color: "text-secondary" },
    { skill: "AWS", demand: "Growing", trend: "+12%", color: "text-accent" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Career Marketplace</h1>
          <p className="text-muted-foreground">Find your perfect job match with AI-powered recommendations</p>
        </div>

        {/* Search Bar */}
        <Card className="p-6 shadow-card mb-6">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
                <Input placeholder="Search for jobs, companies, or skills..." className="pl-10" />
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1">
                <Filter size={16} />
                Filters
              </Button>
              <Button variant="hero" className="flex-1">
                <Search size={16} />
                Search
              </Button>
            </div>
          </div>
        </Card>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content - Jobs List */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="matches" className="space-y-6">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="matches">Top Matches</TabsTrigger>
                <TabsTrigger value="recent">Recent</TabsTrigger>
                <TabsTrigger value="saved">Saved</TabsTrigger>
              </TabsList>

              <TabsContent value="matches" className="space-y-4">
                {jobs.map((job, index) => (
                  <Card key={index} className="p-6 shadow-card hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex gap-4">
                        <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center flex-shrink-0">
                          <Building className="text-primary-foreground" size={24} />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg mb-1">{job.title}</h3>
                          <p className="text-muted-foreground mb-2">{job.company}</p>
                          <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <MapPin size={14} />
                              {job.location}
                            </span>
                            <span className="flex items-center gap-1">
                              <Briefcase size={14} />
                              {job.type}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock size={14} />
                              {job.posted}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-secondary mb-1">{job.match}%</div>
                        <div className="text-xs text-muted-foreground">Match</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mb-4">
                      <DollarSign size={16} className="text-accent" />
                      <span className="font-semibold">{job.salary}</span>
                    </div>

                    <div className="flex flex-wrap gap-2 mb-4">
                      {job.skills.map((skill, i) => (
                        <Badge key={i} variant="secondary">{skill}</Badge>
                      ))}
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t">
                      <span className="text-sm text-muted-foreground">{job.applicants} applicants</span>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm">
                          <Heart size={16} />
                        </Button>
                        <Button variant="outline" size="sm">
                          View Details
                        </Button>
                        <Button variant="hero" size="sm">
                          Apply Now
                          <ExternalLink size={14} />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </TabsContent>

              <TabsContent value="recent">
                <Card className="p-12 text-center shadow-card">
                  <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-semibold text-lg mb-2">No Recent Searches</h3>
                  <p className="text-muted-foreground">Your recently viewed jobs will appear here</p>
                </Card>
              </TabsContent>

              <TabsContent value="saved">
                <Card className="p-12 text-center shadow-card">
                  <Heart className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-semibold text-lg mb-2">No Saved Jobs</h3>
                  <p className="text-muted-foreground">Save jobs to easily access them later</p>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Application Tracker */}
            <Card className="p-6 shadow-card">
              <h3 className="font-semibold mb-4">Application Tracker</h3>
              <div className="space-y-3">
                {applicationPipeline.map((stage, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${stage.color}`} />
                      <span className="text-sm">{stage.stage}</span>
                    </div>
                    <span className="font-semibold">{stage.count}</span>
                  </div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4">View All Applications</Button>
            </Card>

            {/* Market Insights */}
            <Card className="p-6 shadow-card">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="text-accent" size={20} />
                <h3 className="font-semibold">Market Insights</h3>
              </div>
              <div className="space-y-3">
                {marketInsights.map((insight, index) => (
                  <div key={index} className="p-3 bg-muted rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{insight.skill}</span>
                      <span className={`text-sm font-semibold ${insight.color}`}>
                        {insight.trend}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">{insight.demand} Demand</p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Recommended Actions */}
            <Card className="p-6 shadow-card bg-gradient-secondary text-secondary-foreground">
              <h3 className="font-semibold mb-3">Boost Your Profile</h3>
              <p className="text-sm mb-4 text-secondary-foreground/90">
                Complete your profile to increase your chances of getting hired
              </p>
              <Button variant="accent" className="w-full">
                Complete Profile
              </Button>
            </Card>

            {/* Job Alerts */}
            <Card className="p-6 shadow-card">
              <h3 className="font-semibold mb-3">Job Alerts</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Get notified about new jobs matching your profile
              </p>
              <Button variant="outline" className="w-full">
                Set Up Alerts
              </Button>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobMarketplace;
