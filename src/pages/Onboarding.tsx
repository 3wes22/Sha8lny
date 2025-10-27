import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Globe, User, Target, Sparkles, ArrowRight, ArrowLeft } from "lucide-react";

const Onboarding = () => {
  const [step, setStep] = useState(1);
  const [selectedLanguage, setSelectedLanguage] = useState("en");
  const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
  const navigate = useNavigate();

  const totalSteps = 5;
  const progress = (step / totalSteps) * 100;

  const goals = [
    "Find a new job",
    "Learn new skills",
    "Get promoted",
    "Switch careers",
    "Start freelancing",
    "Improve salary",
  ];

  const skills = [
    "JavaScript", "React", "Python", "Node.js", "TypeScript", "AWS",
    "Docker", "SQL", "Git", "CSS", "HTML", "REST APIs"
  ];

  const toggleGoal = (goal: string) => {
    setSelectedGoals(prev => 
      prev.includes(goal) 
        ? prev.filter(g => g !== goal)
        : [...prev, goal]
    );
  };

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      navigate("/dashboard");
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl p-8 shadow-lg">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Step {step} of {totalSteps}</span>
            <span className="text-sm text-muted-foreground">{Math.round(progress)}% Complete</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Step 1: Language Selection */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Globe className="text-primary" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Choose Your Language</h2>
              <p className="text-muted-foreground">Select your preferred language for the platform</p>
            </div>

            <RadioGroup value={selectedLanguage} onValueChange={setSelectedLanguage} className="space-y-3">
              <div className="flex items-center space-x-3 p-4 border rounded-lg cursor-pointer hover:border-primary">
                <RadioGroupItem value="en" id="en" />
                <Label htmlFor="en" className="flex-1 cursor-pointer">
                  <div className="font-medium">English</div>
                  <div className="text-sm text-muted-foreground">English language interface</div>
                </Label>
              </div>
              <div className="flex items-center space-x-3 p-4 border rounded-lg cursor-pointer hover:border-primary">
                <RadioGroupItem value="ar" id="ar" />
                <Label htmlFor="ar" className="flex-1 cursor-pointer">
                  <div className="font-medium">العربية</div>
                  <div className="text-sm text-muted-foreground">Arabic language interface</div>
                </Label>
              </div>
            </RadioGroup>
          </div>
        )}

        {/* Step 2: Profile Setup */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="text-secondary" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Complete Your Profile</h2>
              <p className="text-muted-foreground">Tell us a bit about yourself</p>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current-role">Current Role</Label>
                <Input id="current-role" placeholder="e.g., Frontend Developer" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="experience">Years of Experience</Label>
                <Input id="experience" type="number" placeholder="e.g., 3" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="education">Highest Education</Label>
                <Input id="education" placeholder="e.g., Bachelor's in Computer Science" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input id="location" placeholder="e.g., Cairo, Egypt" />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Career Goals */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Target className="text-accent" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">What Are Your Goals?</h2>
              <p className="text-muted-foreground">Select all that apply to personalize your experience</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {goals.map((goal) => (
                <button
                  key={goal}
                  onClick={() => toggleGoal(goal)}
                  className={`p-4 border rounded-lg text-center transition-all ${
                    selectedGoals.includes(goal)
                      ? "border-primary bg-primary/10"
                      : "hover:border-primary/50"
                  }`}
                >
                  <div className="font-medium">{goal}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Skill Snapshot */}
        {step === 4 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="text-primary" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Select Your Skills</h2>
              <p className="text-muted-foreground">Choose the skills you're proficient in</p>
            </div>

            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <Badge
                  key={skill}
                  variant="outline"
                  className="cursor-pointer hover:bg-secondary hover:text-secondary-foreground transition-colors px-4 py-2"
                >
                  {skill}
                </Badge>
              ))}
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                💡 Don't worry if you can't find all your skills here. You'll be able to add more in your profile later.
              </p>
            </div>
          </div>
        )}

        {/* Step 5: Assessment Intro */}
        {step === 5 && (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Target className="text-secondary" size={32} />
              </div>
              <h2 className="text-2xl font-bold mb-2">Ready for Your First Assessment?</h2>
              <p className="text-muted-foreground">
                Take a quick skill assessment to help us personalize your learning path
              </p>
            </div>

            <Card className="p-6 bg-muted/50">
              <h3 className="font-semibold mb-4">What to Expect:</h3>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-primary text-sm">✓</span>
                  </div>
                  <div>
                    <p className="font-medium">15-20 minutes</p>
                    <p className="text-sm text-muted-foreground">Quick and focused assessment</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-primary text-sm">✓</span>
                  </div>
                  <div>
                    <p className="font-medium">Adaptive questions</p>
                    <p className="text-sm text-muted-foreground">Questions adjust to your skill level</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-primary text-sm">✓</span>
                  </div>
                  <div>
                    <p className="font-medium">Instant results</p>
                    <p className="text-sm text-muted-foreground">Get your personalized learning path immediately</p>
                  </div>
                </li>
              </ul>
            </Card>

            <div className="flex items-center justify-between p-4 bg-accent/10 rounded-lg">
              <span className="text-sm font-medium">You can skip this for now</span>
              <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>
                Skip
              </Button>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t">
          <Button
            variant="ghost"
            onClick={handleBack}
            disabled={step === 1}
          >
            <ArrowLeft size={16} />
            Back
          </Button>
          <Button
            variant="hero"
            onClick={handleNext}
          >
            {step === totalSteps ? "Go to Dashboard" : "Continue"}
            <ArrowRight size={16} />
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Onboarding;
