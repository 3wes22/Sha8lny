/**
 * Sha8lny PPTX Generator - Direct PptxGenJS Version
 * Creates PowerPoint slides from the refined PRESENTATION.md content
 */

const pptxgen = require('pptxgenjs');

// Design palette: Dark professional theme
const COLORS = {
    bg: '1C2833',
    accent: '277884',
    accentLight: '5EA8A7',
    text: 'ffffff',
    textMuted: 'AAB7B8',
    success: '27AE60',
    danger: 'E74C3C',
    tableHeader: '277884',
    tableRow: '2E4053',
    tableBorder: '3E5063'
};

// Helper function to add a title slide
function addTitleSlide(pptx, title, subtitle, content) {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.bg };

    // Accent bar
    slide.addShape(pptx.shapes.RECTANGLE, {
        x: 0, y: 0, w: '100%', h: 0.12,
        fill: { color: COLORS.accent }
    });

    // Title (Arabic style)
    slide.addText(title, {
        x: 0.5, y: 2.2, w: 9, h: 0.8,
        fontSize: 48, fontFace: 'Arial', bold: true, color: COLORS.accentLight,
        align: 'center'
    });

    // Subtitle
    slide.addText(subtitle, {
        x: 0.5, y: 3.0, w: 9, h: 0.6,
        fontSize: 28, fontFace: 'Arial', bold: true, color: COLORS.text,
        align: 'center'
    });

    // Content
    slide.addText(content, {
        x: 0.5, y: 4.2, w: 9, h: 0.6,
        fontSize: 14, fontFace: 'Arial', color: COLORS.textMuted,
        align: 'center'
    });

    return slide;
}

// Helper function to add a content slide with bullets
function addBulletSlide(pptx, title, subtitle, bullets) {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.bg };

    // Accent bar
    slide.addShape(pptx.shapes.RECTANGLE, {
        x: 0, y: 0, w: '100%', h: 0.12,
        fill: { color: COLORS.accent }
    });

    // Title
    slide.addText(title, {
        x: 0.4, y: 0.35, w: 9, h: 0.5,
        fontSize: 28, fontFace: 'Arial', bold: true, color: COLORS.text
    });

    // Subtitle (if provided)
    if (subtitle) {
        slide.addText(subtitle, {
            x: 0.4, y: 0.85, w: 9, h: 0.35,
            fontSize: 16, fontFace: 'Arial', color: COLORS.accentLight
        });
    }

    // Bullets
    const bulletY = subtitle ? 1.4 : 1.1;
    const bulletItems = bullets.map(b => ({ text: b, options: { bullet: { type: 'none' }, indentLevel: 0 } }));

    slide.addText(bulletItems, {
        x: 0.5, y: bulletY, w: 9, h: 3.5,
        fontSize: 16, fontFace: 'Arial', color: COLORS.text,
        paraSpaceAfter: 12,
        bullet: { type: 'bullet', color: COLORS.accentLight }
    });

    return slide;
}

// Helper function to add a table slide
function addTableSlide(pptx, title, headers, rows) {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.bg };

    // Accent bar
    slide.addShape(pptx.shapes.RECTANGLE, {
        x: 0, y: 0, w: '100%', h: 0.12,
        fill: { color: COLORS.accent }
    });

    // Title
    slide.addText(title, {
        x: 0.4, y: 0.35, w: 9, h: 0.5,
        fontSize: 26, fontFace: 'Arial', bold: true, color: COLORS.text
    });

    // Build table data
    const tableData = [
        headers.map(h => ({ text: h, options: { fill: { color: COLORS.tableHeader }, color: COLORS.text, bold: true } })),
        ...rows.map(row => row.map(cell => ({ text: cell, options: { fill: { color: COLORS.tableRow }, color: COLORS.text } })))
    ];

    // Calculate column widths
    const numCols = headers.length;
    const colW = Array(numCols).fill(9 / numCols);

    slide.addTable(tableData, {
        x: 0.4, y: 1.0, w: 9.2,
        colW: colW,
        border: { pt: 0.5, color: COLORS.tableBorder },
        fontSize: 11,
        fontFace: 'Arial',
        valign: 'middle'
    });

    return slide;
}

// Helper function for diagram placeholder
function addDiagramSlide(pptx, title, subtitle, diagramName) {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.bg };

    // Accent bar
    slide.addShape(pptx.shapes.RECTANGLE, {
        x: 0, y: 0, w: '100%', h: 0.12,
        fill: { color: COLORS.accent }
    });

    // Title
    slide.addText(title, {
        x: 0.4, y: 0.35, w: 9, h: 0.5,
        fontSize: 26, fontFace: 'Arial', bold: true, color: COLORS.text
    });

    // Subtitle
    if (subtitle) {
        slide.addText(subtitle, {
            x: 0.4, y: 0.85, w: 9, h: 0.35,
            fontSize: 16, fontFace: 'Arial', color: COLORS.accentLight
        });
    }

    // Diagram placeholder
    slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
        x: 0.5, y: 1.4, w: 9, h: 3.6,
        fill: { color: '2E4053' },
        line: { color: COLORS.accent, width: 2, dashType: 'dash' }
    });

    slide.addText(`[${diagramName} Diagram]`, {
        x: 0.5, y: 2.8, w: 9, h: 0.5,
        fontSize: 18, fontFace: 'Arial', color: COLORS.textMuted,
        align: 'center'
    });

    return slide;
}

// Helper for thank you slide
function addThankYouSlide(pptx) {
    const slide = pptx.addSlide();
    slide.background = { color: COLORS.bg };

    // Accent bar
    slide.addShape(pptx.shapes.RECTANGLE, {
        x: 0, y: 0, w: '100%', h: 0.12,
        fill: { color: COLORS.accent }
    });

    slide.addText('شكراً لاستماعكم 🙏', {
        x: 0.5, y: 1.8, w: 9, h: 0.8,
        fontSize: 42, fontFace: 'Arial', bold: true, color: COLORS.text,
        align: 'center'
    });

    slide.addText('Thank You for Listening!', {
        x: 0.5, y: 2.6, w: 9, h: 0.5,
        fontSize: 24, fontFace: 'Arial', color: COLORS.accentLight,
        align: 'center'
    });

    slide.addText('Questions?', {
        x: 0.5, y: 3.4, w: 9, h: 0.5,
        fontSize: 28, fontFace: 'Arial', bold: true, color: COLORS.text,
        align: 'center'
    });

    slide.addText('Team Sha8lny\nNile University | ITCS Department | 2025', {
        x: 0.5, y: 4.2, w: 9, h: 0.6,
        fontSize: 14, fontFace: 'Arial', color: COLORS.textMuted,
        align: 'center'
    });

    return slide;
}

async function createPresentation() {
    console.log('Creating Sha8lny Presentation...\n');

    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.author = 'Team Sha8lny';
    pptx.title = 'Sha8lny - AI-Powered Career Empowerment Platform';
    pptx.subject = 'Nile University Graduation Project 2025';

    // ============= SECTION 1: Introduction =============
    console.log('Section 1: Introduction...');

    // Slide 1: Title
    addTitleSlide(pptx,
        'Sha8lny - شغّلني',
        'AI-Powered Career Empowerment Platform',
        'Nile University Graduation Project 2025 | ITCS Department'
    );

    // Slide 2: Career Crisis
    addBulletSlide(pptx,
        'The Career Crisis',
        'Egypt\'s Youth Employment Challenge',
        [
            '📊 27% Youth Unemployment Rate in Egypt',
            '🎓 700,000+ Graduates Enter Job Market Yearly',
            '❌ 60% of Graduates Work in Unrelated Fields',
            '',
            '→ Students don\'t know what skills they need',
            '→ Companies can\'t find qualified candidates'
        ]
    );

    // Slide 3: Problem
    addBulletSlide(pptx,
        'The Problem We\'re Solving',
        null,
        [
            '❌ No clear career direction → Wasted years',
            '❌ Outdated curriculum → Skills mismatch',
            '❌ Overwhelming resources → Don\'t know where to start',
            '❌ No practical guidance → Generic advice',
            '',
            '✅ What Students Need:',
            '   • Personalized career assessment',
            '   • Skills-to-job mapping',
            '   • AI-guided learning paths'
        ]
    );

    // Slide 4: Solution
    addBulletSlide(pptx,
        'Introducing Sha8lny',
        'Your AI Career Companion for the Egyptian Market',
        [
            '🧠 AI Career Assessment — Evaluate skills & gaps',
            '📈 Personalized Roadmaps — Step-by-step learning',
            '💼 Egyptian Job Integration — Wuzzuf, Bayt',
            '🤖 AI Career Advisor — 24/7 career chatbot',
            '📚 Smart Course Matching — Udemy, Coursera',
            '📊 Market Insights — Trending skills & salaries'
        ]
    );

    // Slide 5: Scope
    addTableSlide(pptx,
        'Project Scope — Academic Deliverables Matrix',
        ['Deliverable Category', 'Academic Output', 'Status'],
        [
            ['Requirements Engineering', 'SRS Document', '✅'],
            ['Architectural Methodology', 'ERD, HLD Documents', '✅'],
            ['Backend Implementation', 'Django API (10 Modules)', '✅'],
            ['Frontend Development', 'React UI (15 Pages)', '✅'],
            ['AI Infrastructure', 'RAG + ChromaDB', '✅']
        ]
    );

    // ============= SECTION 2: Architecture =============
    console.log('Section 2: Architecture...');

    // Slide 6: Architecture
    addDiagramSlide(pptx,
        'High-Level Architecture',
        'Modular Monolithic Design',
        'Architecture'
    );

    // Slide 7: Monolith Selection
    addTableSlide(pptx,
        'Modular Monolith Selection',
        ['Criterion', 'Modular Monolith', 'Decision Factor'],
        [
            ['Development Velocity', '✅ Single codebase', 'MVP timeline (16 weeks)'],
            ['ACID Compliance', '✅ Native PostgreSQL', 'Data integrity critical'],
            ['Operational Overhead', '✅ Single deployment', 'Team size (<6)'],
            ['Latency Profile', '✅ In-process calls', 'Real-time UX'],
            ['Infrastructure Cost', '✅ Single compute', 'Academic budget']
        ]
    );

    // Slide 8: Tech Stack
    addTableSlide(pptx,
        'Technology Stack',
        ['Layer', 'Technologies'],
        [
            ['Frontend', 'React 18, Vite, TypeScript, TailwindCSS, shadcn/ui'],
            ['Backend', 'Django 5.x, Django REST Framework, JWT Auth'],
            ['Database', 'PostgreSQL (primary), Redis (cache/queue)'],
            ['AI/ML', 'LM Studio, ChromaDB, Sentence Transformers'],
            ['Data Sources', 'O*NET, roadmap.sh, Wuzzuf, Bayt']
        ]
    );

    // Slide 9: Data Flow
    addDiagramSlide(pptx,
        'Data Flow: Assessment → Roadmap',
        null,
        'Data Flow'
    );

    // Slide 10: ERD
    addDiagramSlide(pptx,
        'Entity Relationship Diagram',
        null,
        'ERD'
    );

    // ============= SECTION 3: Backend =============
    console.log('Section 3: Backend Development...');

    // Slide 11: API Design
    addTableSlide(pptx,
        'RESTful API Architecture',
        ['Module', 'Endpoint Pattern', 'Authentication'],
        [
            ['Users', '/api/v1/users/', 'JWT (Auth0-ready)'],
            ['Assessments', '/api/v1/assessments/', 'JWT Required'],
            ['Roadmaps', '/api/v1/roadmaps/', 'JWT Required'],
            ['Advisory', '/api/v1/advisory/chat/', 'JWT + Throttling'],
            ['Jobs', '/api/v1/jobs/', 'Public + JWT Enhanced'],
            ['Courses', '/api/v1/courses/', 'Public']
        ]
    );

    // Slide 12: Celery
    addBulletSlide(pptx,
        'Asynchronous Task Processing Architecture',
        'Celery + Redis Task Queue',
        [
            '→ Django API → Redis Broker → Celery Worker Pool',
            '',
            'Task Types:',
            '• assessment_analysis.task (LLM skill evaluation)',
            '• roadmap_generation.task (RAG-enhanced planning)',
            '• job_scraping.task (Wuzzuf/Bayt ingestion)',
            '• notification_dispatch.task (Email/Push delivery)',
            '',
            '✅ Non-blocking API responses for AI inference',
            '✅ Horizontal scalability via worker pool'
        ]
    );

    // Slide 13: Database
    addTableSlide(pptx,
        'PostgreSQL Database Engineering',
        ['Design Pattern', 'Implementation', 'Rationale'],
        [
            ['UUID Primary Keys', 'uuid.uuid4() on all models', 'Distributed-ready'],
            ['JSONB Metadata', 'Assessment.responses, Roadmap.ai_metadata', 'Schema flexibility'],
            ['Soft Delete', 'BaseModel.is_deleted flag', 'Audit trail'],
            ['Strategic Indexing', '40+ custom indexes', 'O(log n) lookups'],
            ['Composite Constraints', 'unique_together, UniqueConstraint', 'Data integrity']
        ]
    );

    // ============= SECTION 4: Frontend =============
    console.log('Section 4: Frontend Development...');

    // Slide 14: Frontend Pages
    addTableSlide(pptx,
        'Frontend Page Architecture (15 Pages)',
        ['Cluster', 'Pages', 'User Journey'],
        [
            ['User Assessment', 'Assessment, Session, Results', 'Evaluation → Analysis → Results'],
            ['Job Discovery', 'Jobs, SavedJobs', 'Search → Bookmark → Apply'],
            ['AI Advisory', 'Advisor', 'RAG-powered chatbot'],
            ['User Management', 'Login, Register, Profile, Settings', 'Auth → Preferences'],
            ['Learning Path', 'Roadmap', 'Roadmap visualization'],
            ['Core Navigation', 'Dashboard, Index, NotFound', 'Entry points']
        ]
    );

    // ============= SECTION 5: AI/RAG =============
    console.log('Section 5: AI/RAG System...');

    // Slide 15: RAG Overview
    addDiagramSlide(pptx,
        'RAG Architecture Overview',
        'Retrieval-Augmented Generation Pipeline',
        'RAG Pipeline'
    );

    // Slide 16: Knowledge Base
    addTableSlide(pptx,
        'Knowledge Base Engineering',
        ['Parameter', 'Value', 'Source'],
        [
            ['Collection Name', 'career_knowledge', 'build_vector_db.py'],
            ['Chunk Size', '500 characters', 'CHUNK_SIZE constant'],
            ['Chunk Overlap', '50 characters', 'CHUNK_OVERLAP constant'],
            ['Embedding Model', 'all-MiniLM-L6-v2', 'Sentence Transformers'],
            ['Embedding Dimensions', '384', 'Model specification'],
            ['Batch Size', '100 documents', 'Memory optimization']
        ]
    );

    // Slide 17: Source Selection
    addBulletSlide(pptx,
        'Smart Source Selection',
        'Intelligent Query Routing',
        [
            'Learning keywords → roadmap.sh collection',
            'Job keywords → O*NET collection',
            'General queries → All collections',
            '',
            '⚡ Faster queries (smaller search space)',
            '🎯 More relevant results',
            '📈 Better answer quality'
        ]
    );

    // Slide 18: Anti-Hallucination
    addTableSlide(pptx,
        'Anti-Hallucination Prompt Engineering',
        ['Parameter', 'Value', 'Rationale'],
        [
            ['Temperature', '0.3', 'Balanced: factual but natural'],
            ['Max Tokens', '400', 'Sufficient for detailed responses'],
            ['TOP_K Retrieval', '3', 'Quality over quantity'],
            ['Timeout', '30 seconds', 'Prevent hanging requests']
        ]
    );

    // Slide 19: LM Studio
    addBulletSlide(pptx,
        'LM Studio Local Inference',
        'Configuration',
        [
            '📦 Tested Models:',
            '   • Gemma-2-2b-it',
            '   • Qwen2.5-1.5B-Instruct',
            '',
            '⚙️ Runtime Parameters:',
            '   • Context Length: 4096 tokens',
            '   • Temperature: 0.3',
            '   • Max Tokens: 400',
            '   • API: localhost:1234/v1/chat/completions',
            '',
            '✅ Zero API costs | ✅ Full data privacy | ✅ Offline capable'
        ]
    );

    // ============= SECTION 6: Demo & Conclusion =============
    console.log('Section 6: Demo & Conclusion...');

    // Slide 20: Demo
    addTableSlide(pptx,
        'Live Demonstration Flow',
        ['Priority', 'Feature', 'Duration'],
        [
            ['1️⃣', 'AI Career Advisor', '90 sec'],
            ['2️⃣', 'Skill Assessment', '60 sec'],
            ['3️⃣', 'Personalized Roadmap', '45 sec'],
            ['4️⃣', 'Job Matching', '30 sec'],
            ['5️⃣', 'User Dashboard', '15 sec']
        ]
    );

    // Slide 21: Achievements
    addBulletSlide(pptx,
        'First Half Achievements',
        'Completed Deliverables',
        [
            '✅ Architectural Design — Modular Monolithic Architecture',
            '✅ Backend Implementation — Django RESTful API (10 Modules)',
            '✅ Frontend Development — React TypeScript (15 Pages)',
            '✅ Database Engineering — PostgreSQL + JSONB (25+ Models)',
            '✅ RAG Pipeline — ChromaDB + Sentence Transformers',
            '✅ AI Integration — LM Studio Local Inference'
        ]
    );

    // Slide 22: Challenges
    addTableSlide(pptx,
        'Challenges & Solutions',
        ['Challenge', 'Solution'],
        [
            ['📉 LLM Hallucination', 'Anti-hallucination prompts + temperature=0.3'],
            ['⏱️ Slow AI Responses', 'Background processing with Celery'],
            ['📚 Data Quality', 'Multiple sources (O*NET, roadmap.sh)'],
            ['🔗 Integration Complexity', 'Service layer pattern'],
            ['💰 API Costs', 'Local LLM inference with LM Studio']
        ]
    );

    // Slide 23: Next Phase
    addBulletSlide(pptx,
        'Second Half Development Roadmap',
        null,
        [
            'Phase 1: Frontend-Backend Integration (Weeks 1-2)',
            'Phase 2: Auth0 Universal Login (Weeks 2-3)',
            '   • Social providers (Google, LinkedIn)',
            '   • JWT refresh token rotation',
            'Phase 3: Job Scraping - Wuzzuf, Bayt (Weeks 3-4)',
            'Phase 4: Docker + AWS Deployment (Weeks 5-7)',
            '   • ECS Fargate, RDS PostgreSQL, ElastiCache',
            'Phase 5: User Acceptance Testing (Weeks 7-8)'
        ]
    );

    // Slide 24: Conclusion
    addBulletSlide(pptx,
        'Sha8lny Vision',
        'Empowering Egyptian graduates with AI-driven career guidance',
        [
            '🎯 Solving Real Problems: 27% youth unemployment in Egypt',
            '🤖 AI-Powered: RAG + LLM for personalized guidance',
            '🏗️ Solid Architecture: Modular monolith, ready to scale',
            '📊 Data-Driven: O*NET + roadmap.sh + Egyptian market',
            '🚀 On Track: First half milestones completed'
        ]
    );

    // Slide 25: Thank You
    addThankYouSlide(pptx);

    // Save
    const outputPath = 'Sha8lny_Presentation_Refined.pptx';
    await pptx.writeFile({ fileName: outputPath });

    console.log('\n============================================');
    console.log('✅ Presentation created successfully!');
    console.log(`   Output: ${outputPath}`);
    console.log('   Total slides: 25');
    console.log('============================================');
}

createPresentation().catch(err => {
    console.error('Error:', err);
    process.exit(1);
});
