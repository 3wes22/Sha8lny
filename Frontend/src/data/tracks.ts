export type VideoResource = {
  id: string;
  title: string;
  url: string;
  duration?: string;
  source?: string;
  level?: "Beginner" | "Intermediate" | "Advanced";
};

export type Stage = {
  id: string;
  title: string;
  summary: string;
  estimated: string;
  level: "Beginner" | "Intermediate" | "Advanced";
  keyTopics: string[];
  videos?: VideoResource[];
};

export type Track = {
  id: string;
  label: string;
  category:
    | "Web"
    | "Data"
    | "AI"
    | "Mobile"
    | "Security"
    | "Product"
    | "Design"
    | "Engineering"
    | "DevOps"
    | "Other";
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  accent: "violet" | "cyan" | "emerald" | "amber" | "rose" | "blue";
  description: string;
  stages: Stage[];
};

// Helper: minimal placeholder stages for tracks we haven't filled yet
const placeholderStages = (trackName: string): Stage[] => [
  {
    id: "foundations",
    title: "Foundations",
    summary: `Core fundamentals you must understand before going deep in ${trackName}.`,
    estimated: "~1–2 weeks",
    level: "Beginner",
    keyTopics: ["Fundamentals", "Tooling", "Core concepts", "Practice projects"],
  },
  {
    id: "core-skills",
    title: "Core Skills",
    summary: `The main skills required to become job-ready in ${trackName}.`,
    estimated: "~3–5 weeks",
    level: "Intermediate",
    keyTopics: ["Key technologies", "Best practices", "Workflows", "Problem solving"],
  },
  {
    id: "job-ready",
    title: "Job-Ready Projects",
    summary: `Portfolio projects + interview preparation for ${trackName}.`,
    estimated: "~2–3 weeks",
    level: "Intermediate",
    keyTopics: ["Portfolio", "Testing", "Deployment", "Interview prep"],
  },
];

export const TRACKS: Track[] = [
  // ======================
  // WEB / SOFTWARE
  // ======================
  {
    id: "frontend",
    label: "Frontend",
    category: "Web",
    difficulty: "Beginner",
    accent: "violet",
    description: "Build beautiful UIs with HTML/CSS/JS and modern frameworks.",
    stages: [
      {
        id: "internet-web-basics",
        title: "Internet & Web Basics",
        summary: "Understand HTTP, DNS, domains, hosting, and how browsers work.",
        estimated: "~3 days",
        level: "Beginner",
        keyTopics: [
          "How the internet works",
          "HTTP/HTTPS",
          "Domains & DNS",
          "Hosting basics",
          "Browsers & rendering",
        ],
        videos: [
          {
            id: "internet-5m",
            title: "How the Internet Works in 5 Minutes",
            url: "https://www.youtube.com/watch?v=7_LPdttKXPc",
            duration: "5m",
            source: "YouTube",
            level: "Beginner",
          },
        ],
      },
      {
        id: "html-css",
        title: "HTML & CSS",
        summary: "Layout, responsive design, and clean UI structure.",
        estimated: "~1 week",
        level: "Beginner",
        keyTopics: ["Semantic HTML", "Flexbox", "Grid", "Responsive design", "Forms"],
        videos: [
          {
            id: "htmlcss",
            title: "HTML & CSS Full Course",
            url: "https://www.youtube.com/watch?v=mU6anWqZJcc",
            duration: "1h 15m",
            source: "YouTube",
            level: "Beginner",
          },
        ],
      },
      {
        id: "javascript",
        title: "JavaScript Core",
        summary: "The language fundamentals for real interactive UI work.",
        estimated: "~2 weeks",
        level: "Beginner",
        keyTopics: ["Functions", "Arrays/Objects", "DOM", "Events", "Async/await"],
        videos: [
          {
            id: "js",
            title: "JavaScript for Beginners",
            url: "https://www.youtube.com/watch?v=PkZNo7MFNFg",
            duration: "3h 30m",
            source: "YouTube",
            level: "Beginner",
          },
        ],
      },
      {
        id: "react",
        title: "React",
        summary: "Component thinking, state, hooks, and routing.",
        estimated: "~2 weeks",
        level: "Intermediate",
        keyTopics: ["Components", "Props/State", "useEffect", "Routing", "Forms"],
        videos: [
          {
            id: "react-crash",
            title: "React Crash Course",
            url: "https://www.youtube.com/watch?v=w7ejDZ8SWv8",
            duration: "2h",
            source: "YouTube",
            level: "Intermediate",
          },
        ],
      },
      {
        id: "frontend-architecture",
        title: "Architecture & Patterns",
        summary: "Project structure, reusable UI, performance, and best practices.",
        estimated: "~2 weeks",
        level: "Intermediate",
        keyTopics: ["Folder structure", "State patterns", "Performance", "UX polish"],
      },
    ],
  },
  {
    id: "backend",
    label: "Backend",
    category: "Web",
    difficulty: "Intermediate",
    accent: "cyan",
    description: "Build APIs, auth, database integrations, and scalable services.",
    stages: [
      {
        id: "backend-basics",
        title: "Backend Fundamentals",
        summary: "Client-server model, REST APIs, and request lifecycle.",
        estimated: "~4 days",
        level: "Beginner",
        keyTopics: ["REST", "HTTP lifecycle", "Status codes", "API design"],
      },
      {
        id: "node-express",
        title: "Node.js & Express",
        summary: "Routing, controllers, middleware, and error handling.",
        estimated: "~1.5 weeks",
        level: "Intermediate",
        keyTopics: ["Routing", "Middleware", "Auth basics", "Validation"],
        videos: [
          {
            id: "express",
            title: "Express.js Crash Course",
            url: "https://www.youtube.com/watch?v=L72fhGm1tfE",
            duration: "1h 20m",
            source: "YouTube",
            level: "Intermediate",
          },
        ],
      },
      {
        id: "db",
        title: "Database Integration",
        summary: "Store data safely with SQL/NoSQL and basic schema design.",
        estimated: "~2 weeks",
        level: "Intermediate",
        keyTopics: ["SQL vs NoSQL", "Schema", "ORM basics", "Indexes"],
      },
      {
        id: "auth",
        title: "Auth & Security Basics",
        summary: "JWT, sessions, protected routes, and secure patterns.",
        estimated: "~1 week",
        level: "Intermediate",
        keyTopics: ["JWT", "Sessions", "Hashing", "Authorization"],
      },
    ],
  },
  {
    id: "full-stack",
    label: "Full Stack",
    category: "Web",
    difficulty: "Intermediate",
    accent: "emerald",
    description: "Frontend + backend + deployment, end-to-end product building.",
    stages: placeholderStages("Full Stack"),
  },

  // ======================
  // DATA
  // ======================
  {
    id: "data-analyst",
    label: "Data Analyst",
    category: "Data",
    difficulty: "Beginner",
    accent: "blue",
    description: "Analyze data, build dashboards, and present insights clearly.",
    stages: placeholderStages("Data Analyst"),
  },
  {
    id: "data-engineer",
    label: "Data Engineer",
    category: "Data",
    difficulty: "Advanced",
    accent: "cyan",
    description: "Data pipelines, warehouses, ETL/ELT, and large-scale processing.",
    stages: placeholderStages("Data Engineer"),
  },
  {
    id: "data-scientist",
    label: "Data Scientist",
    category: "Data",
    difficulty: "Intermediate",
    accent: "violet",
    description: "Statistics, ML fundamentals, experiments, and predictive models.",
    stages: placeholderStages("Data Scientist"),
  },
  {
    id: "bi-analyst",
    label: "BI Analyst",
    category: "Data",
    difficulty: "Beginner",
    accent: "blue",
    description: "Business reporting, dashboards, KPIs, and storytelling with data.",
    stages: placeholderStages("BI Analyst"),
  },
  {
    id: "postgresql",
    label: "PostgreSQL",
    category: "Data",
    difficulty: "Intermediate",
    accent: "blue",
    description: "SQL mastery, indexes, schema design, and query optimization.",
    stages: placeholderStages("PostgreSQL"),
  },

  // ======================
  // AI / ML
  // ======================
  {
    id: "ai-engineer",
    label: "AI Engineer",
    category: "AI",
    difficulty: "Advanced",
    accent: "rose",
    description: "Build AI products, integrate models, and deploy AI systems.",
    stages: placeholderStages("AI Engineer"),
  },
  {
    id: "ml-engineer",
    label: "Machine Learning",
    category: "AI",
    difficulty: "Advanced",
    accent: "rose",
    description: "Train models, evaluate, and deploy ML pipelines.",
    stages: placeholderStages("Machine Learning"),
  },
  {
    id: "ai-data-scientist",
    label: "AI & Data Scientist",
    category: "AI",
    difficulty: "Advanced",
    accent: "violet",
    description: "Deep data science + ML + AI product thinking.",
    stages: placeholderStages("AI & Data Scientist"),
  },
  {
    id: "mlops",
    label: "MLOps",
    category: "AI",
    difficulty: "Advanced",
    accent: "amber",
    description: "CI/CD for ML, model monitoring, deployments, and pipelines.",
    stages: placeholderStages("MLOps"),
  },

  // ======================
  // DEVOPS
  // ======================
  {
    id: "devops",
    label: "DevOps",
    category: "DevOps",
    difficulty: "Advanced",
    accent: "amber",
    description: "CI/CD, Docker, cloud basics, and production operations.",
    stages: placeholderStages("DevOps"),
  },

  // ======================
  // MOBILE
  // ======================
  {
    id: "android",
    label: "Android",
    category: "Mobile",
    difficulty: "Intermediate",
    accent: "emerald",
    description: "Build Android apps and publish mobile products.",
    stages: placeholderStages("Android"),
  },
  {
    id: "ios",
    label: "iOS",
    category: "Mobile",
    difficulty: "Intermediate",
    accent: "blue",
    description: "Build iOS apps with modern Apple tooling and patterns.",
    stages: placeholderStages("iOS"),
  },

  // ======================
  // SECURITY
  // ======================
  {
    id: "cyber-security",
    label: "Cyber Security",
    category: "Security",
    difficulty: "Advanced",
    accent: "rose",
    description: "Security fundamentals, threats, and defensive strategies.",
    stages: placeholderStages("Cyber Security"),
  },

  // ======================
  // DESIGN / UX
  // ======================
  {
    id: "ux-design",
    label: "UX Design",
    category: "Design",
    difficulty: "Beginner",
    accent: "violet",
    description: "Research, usability, flows, and user-centered design.",
    stages: placeholderStages("UX Design"),
  },
  {
    id: "ui-ux-designer",
    label: "UI/UX Designer",
    category: "Design",
    difficulty: "Beginner",
    accent: "violet",
    description: "Design systems, layouts, and product UI craft.",
    stages: placeholderStages("UI/UX Designer"),
  },
  {
    id: "technical-writer",
    label: "Technical Writer",
    category: "Other",
    difficulty: "Beginner",
    accent: "blue",
    description: "Write clear documentation, guides, and developer content.",
    stages: placeholderStages("Technical Writer"),
  },

  // ======================
  // PRODUCT / MANAGEMENT
  // ======================
  {
    id: "product-manager",
    label: "Product Manager",
    category: "Product",
    difficulty: "Intermediate",
    accent: "emerald",
    description: "Build product strategy, roadmap, and drive execution.",
    stages: placeholderStages("Product Manager"),
  },
  {
    id: "engineering-manager",
    label: "Engineering Manager",
    category: "Engineering",
    difficulty: "Advanced",
    accent: "cyan",
    description: "Lead teams, processes, hiring, and technical delivery.",
    stages: placeholderStages("Engineering Manager"),
  },
  {
    id: "developer-relations",
    label: "Developer Relations",
    category: "Other",
    difficulty: "Intermediate",
    accent: "amber",
    description: "Community, advocacy, content, and developer experience.",
    stages: placeholderStages("Developer Relations"),
  },

  // ======================
  // OTHER TECH PATHS
  // ======================
  {
    id: "software-architect",
    label: "Software Architect",
    category: "Engineering",
    difficulty: "Advanced",
    accent: "cyan",
    description: "System design, architecture patterns, and scaling strategies.",
    stages: placeholderStages("Software Architect"),
  },
  {
    id: "qa",
    label: "QA",
    category: "Engineering",
    difficulty: "Beginner",
    accent: "blue",
    description: "Testing strategy, automation basics, and product quality.",
    stages: placeholderStages("QA"),
  },
  {
    id: "blockchain",
    label: "Blockchain",
    category: "Other",
    difficulty: "Advanced",
    accent: "amber",
    description: "Smart contracts, web3 fundamentals, and blockchain development.",
    stages: placeholderStages("Blockchain"),
  },
  {
    id: "game-developer",
    label: "Game Developer",
    category: "Other",
    difficulty: "Intermediate",
    accent: "violet",
    description: "Game loops, engines, and interactive systems.",
    stages: placeholderStages("Game Developer"),
  },
  {
    id: "server-side-game-developer",
    label: "Server Side Game Developer",
    category: "Other",
    difficulty: "Advanced",
    accent: "cyan",
    description: "Multiplayer servers, real-time networking, and scalability.",
    stages: placeholderStages("Server Side Game Developer"),
  },
];
