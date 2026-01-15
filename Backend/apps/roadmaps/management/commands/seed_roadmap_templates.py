"""
Management command to seed roadmap templates.

Usage:
    python manage.py seed_roadmap_templates
    python manage.py seed_roadmap_templates --clear  # Clear existing templates first
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.roadmaps.models import RoadmapTemplate


class Command(BaseCommand):
    help = 'Seed roadmap templates for common career paths'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing templates before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = RoadmapTemplate.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing templates')
            )

        templates_data = self.get_templates_data()

        created_count = 0
        updated_count = 0

        for template_data in templates_data:
            slug = slugify(template_data['title'])
            template, created = RoadmapTemplate.objects.update_or_create(
                slug=slug,
                defaults=template_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {template.title}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'↻ Updated: {template.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Seeding complete: {created_count} created, {updated_count} updated'
            )
        )

    def get_templates_data(self):
        """Return list of template data dictionaries."""
        return [
            # ===== Backend Developer =====
            {
                'title': 'Backend Developer Roadmap',
                'slug': 'backend-developer-roadmap',
                'description': (
                    'Comprehensive roadmap to become a professional Backend Developer. '
                    'Master server-side programming, databases, APIs, authentication, '
                    'deployment, and cloud services.'
                ),
                'short_description': 'Master backend development with Python, Django, APIs, and databases',
                'target_career': 'Backend Developer',
                'career_level': RoadmapTemplate.ENTRY_LEVEL,
                'estimated_duration_weeks': 24,
                'difficulty_level': 'intermediate',
                'prerequisites': [
                    'Basic programming knowledge (any language)',
                    'Familiarity with command line',
                    'Basic understanding of HTTP and web',
                ],
                'learning_outcomes': [
                    'Build production-ready REST APIs',
                    'Master database design and optimization',
                    'Implement authentication and authorization',
                    'Deploy applications to cloud platforms',
                    'Write clean, maintainable code',
                ],
                'required_skills': [],  # Will be filled with actual skill UUIDs later
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['backend', 'api', 'python', 'django', 'database'],
                    'industry': 'Technology',
                    'salary_range': '60k-120k',
                    'job_openings_estimate': 'High',
                },
            },

            # ===== Frontend Developer =====
            {
                'title': 'Frontend Developer Roadmap',
                'slug': 'frontend-developer-roadmap',
                'description': (
                    'Complete guide to becoming a modern Frontend Developer. '
                    'Learn HTML, CSS, JavaScript, React, TypeScript, and build '
                    'responsive, accessible, and performant user interfaces.'
                ),
                'short_description': 'Build modern web interfaces with React, TypeScript, and CSS',
                'target_career': 'Frontend Developer',
                'career_level': RoadmapTemplate.ENTRY_LEVEL,
                'estimated_duration_weeks': 20,
                'difficulty_level': 'beginner',
                'prerequisites': [
                    'Basic computer skills',
                    'Willingness to learn',
                ],
                'learning_outcomes': [
                    'Build responsive websites from scratch',
                    'Master React and modern JavaScript',
                    'Create accessible user interfaces',
                    'Optimize frontend performance',
                    'Work with design systems and component libraries',
                ],
                'required_skills': [],
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['frontend', 'react', 'javascript', 'typescript', 'css'],
                    'industry': 'Technology',
                    'salary_range': '55k-115k',
                },
            },

            # ===== Full Stack Developer =====
            {
                'title': 'Full Stack Developer Roadmap',
                'slug': 'full-stack-developer-roadmap',
                'description': (
                    'Comprehensive path to become a Full Stack Developer. '
                    'Master both frontend and backend technologies, databases, '
                    'deployment, and full application architecture.'
                ),
                'short_description': 'Master frontend and backend development to build complete applications',
                'target_career': 'Full Stack Developer',
                'career_level': RoadmapTemplate.ENTRY_LEVEL,
                'estimated_duration_weeks': 32,
                'difficulty_level': 'intermediate',
                'prerequisites': [
                    'Basic programming knowledge',
                    'Understanding of web fundamentals',
                ],
                'learning_outcomes': [
                    'Build complete web applications end-to-end',
                    'Master frontend and backend technologies',
                    'Design and implement database schemas',
                    'Deploy and maintain production applications',
                    'Implement CI/CD pipelines',
                ],
                'required_skills': [],
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['fullstack', 'react', 'python', 'database', 'deployment'],
                    'industry': 'Technology',
                    'salary_range': '65k-130k',
                },
            },

            # ===== Data Scientist =====
            {
                'title': 'Data Scientist Roadmap',
                'slug': 'data-scientist-roadmap',
                'description': (
                    'Path to becoming a Data Scientist. Master Python, statistics, '
                    'machine learning, data visualization, and big data technologies. '
                    'Learn to extract insights and build predictive models.'
                ),
                'short_description': 'Learn Python, ML, statistics, and data analysis',
                'target_career': 'Data Scientist',
                'career_level': RoadmapTemplate.ENTRY_LEVEL,
                'estimated_duration_weeks': 28,
                'difficulty_level': 'advanced',
                'prerequisites': [
                    'Strong mathematical foundation',
                    'Basic programming knowledge',
                    'Understanding of statistics',
                ],
                'learning_outcomes': [
                    'Perform exploratory data analysis',
                    'Build machine learning models',
                    'Master data visualization',
                    'Work with big data technologies',
                    'Deploy ML models to production',
                ],
                'required_skills': [],
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['datascience', 'python', 'ml', 'statistics', 'analytics'],
                    'industry': 'Technology',
                    'salary_range': '70k-140k',
                },
            },

            # ===== DevOps Engineer =====
            {
                'title': 'DevOps Engineer Roadmap',
                'slug': 'devops-engineer-roadmap',
                'description': (
                    'Comprehensive guide to becoming a DevOps Engineer. '
                    'Learn CI/CD, cloud platforms, containerization, infrastructure as code, '
                    'monitoring, and automation.'
                ),
                'short_description': 'Master CI/CD, Docker, Kubernetes, and cloud platforms',
                'target_career': 'DevOps Engineer',
                'career_level': RoadmapTemplate.MID_LEVEL,
                'estimated_duration_weeks': 26,
                'difficulty_level': 'advanced',
                'prerequisites': [
                    'Backend development experience',
                    'Linux command line proficiency',
                    'Understanding of networking',
                ],
                'learning_outcomes': [
                    'Implement CI/CD pipelines',
                    'Master Docker and Kubernetes',
                    'Automate infrastructure with Terraform',
                    'Monitor and maintain production systems',
                    'Ensure security and compliance',
                ],
                'required_skills': [],
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['devops', 'docker', 'kubernetes', 'aws', 'cicd'],
                    'industry': 'Technology',
                    'salary_range': '75k-145k',
                },
            },

            # ===== Mobile Developer (Android) =====
            {
                'title': 'Android Developer Roadmap',
                'slug': 'android-developer-roadmap',
                'description': (
                    'Learn Android development with Kotlin. Master Android SDK, '
                    'Jetpack Compose, architecture patterns, testing, and publishing apps '
                    'to Google Play Store.'
                ),
                'short_description': 'Build native Android apps with Kotlin and Jetpack Compose',
                'target_career': 'Android Developer',
                'career_level': RoadmapTemplate.ENTRY_LEVEL,
                'estimated_duration_weeks': 22,
                'difficulty_level': 'intermediate',
                'prerequisites': [
                    'Basic programming knowledge',
                    'Understanding of OOP concepts',
                ],
                'learning_outcomes': [
                    'Build native Android applications',
                    'Master Kotlin programming',
                    'Implement modern UI with Jetpack Compose',
                    'Handle data persistence and networking',
                    'Publish apps to Google Play Store',
                ],
                'required_skills': [],
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['android', 'kotlin', 'mobile', 'jetpack'],
                    'industry': 'Technology',
                    'salary_range': '60k-125k',
                },
            },

            # ===== Machine Learning Engineer =====
            {
                'title': 'Machine Learning Engineer Roadmap',
                'slug': 'machine-learning-engineer-roadmap',
                'description': (
                    'Become a Machine Learning Engineer. Master deep learning, '
                    'neural networks, MLOps, model deployment, and production ML systems.'
                ),
                'short_description': 'Build and deploy ML models with Python, TensorFlow, and MLOps',
                'target_career': 'Machine Learning Engineer',
                'career_level': RoadmapTemplate.MID_LEVEL,
                'estimated_duration_weeks': 30,
                'difficulty_level': 'advanced',
                'prerequisites': [
                    'Strong Python programming',
                    'Understanding of machine learning basics',
                    'Linear algebra and calculus knowledge',
                ],
                'learning_outcomes': [
                    'Build deep learning models',
                    'Implement MLOps pipelines',
                    'Deploy models to production',
                    'Optimize model performance',
                    'Work with large-scale ML systems',
                ],
                'required_skills': [],
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['ml', 'deeplearning', 'python', 'tensorflow', 'mlops'],
                    'industry': 'Technology',
                    'salary_range': '85k-160k',
                },
            },

            # ===== UI/UX Designer =====
            {
                'title': 'UI/UX Designer Roadmap',
                'slug': 'ui-ux-designer-roadmap',
                'description': (
                    'Master UI/UX design principles, tools, and processes. '
                    'Learn user research, wireframing, prototyping, visual design, '
                    'and usability testing.'
                ),
                'short_description': 'Design beautiful and user-friendly interfaces',
                'target_career': 'UI/UX Designer',
                'career_level': RoadmapTemplate.ENTRY_LEVEL,
                'estimated_duration_weeks': 18,
                'difficulty_level': 'beginner',
                'prerequisites': [
                    'Creative mindset',
                    'Basic design principles',
                ],
                'learning_outcomes': [
                    'Conduct user research',
                    'Create wireframes and prototypes',
                    'Design high-fidelity mockups',
                    'Master Figma and design tools',
                    'Perform usability testing',
                ],
                'required_skills': [],
                'is_published': True,
                'usage_count': 0,
                'metadata': {
                    'tags': ['uiux', 'design', 'figma', 'prototyping', 'research'],
                    'industry': 'Technology',
                    'salary_range': '50k-105k',
                },
            },
        ]
