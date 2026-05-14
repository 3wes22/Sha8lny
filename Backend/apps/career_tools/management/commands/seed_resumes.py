"""Seed sample resume data for development/testing."""

from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.career_tools.models import Resume


class Command(BaseCommand):
    help = 'Seeds sample resume data'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing resumes first')

    def handle(self, *args, **options):
        if options['clear']:
            Resume.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared all resumes'))

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No user found. Create a superuser first.'))
            return

        resumes = [
            {
                'title': 'Software Engineer Resume',
                'template_name': 'modern',
                'is_primary': True,
                'personal_info': {
                    'name': 'Ahmed Mohamed',
                    'email': 'ahmed@example.com',
                    'phone': '+20 123 456 7890',
                    'location': 'Cairo, Egypt',
                    'summary': 'Full-stack developer with 3 years of experience building scalable web applications with Django and React. Strong background in AI/ML integration and API design.',
                },
                'work_experience': {
                    'items': [
                        {
                            'role': 'Full-Stack Developer',
                            'company': 'Vodafone Egypt',
                            'start_date': 'Jan 2023',
                            'end_date': 'Present',
                            'location': 'Cairo',
                            'achievements': [
                                'Built customer-facing API serving 500K+ monthly users',
                                'Reduced page load time by 45% through query optimization',
                                'Led migration from monolith to microservices architecture',
                            ],
                        },
                        {
                            'role': 'Backend Developer Intern',
                            'company': 'Instabug',
                            'start_date': 'Jun 2022',
                            'end_date': 'Dec 2022',
                            'location': 'Cairo',
                            'achievements': [
                                'Developed REST APIs using Django REST Framework',
                                'Wrote unit tests achieving 85% code coverage',
                            ],
                        },
                    ]
                },
                'education': {
                    'items': [
                        {
                            'degree': 'B.Sc. Computer Science',
                            'institution': 'Cairo University',
                            'graduation_date': '2022',
                            'field': 'Computer Science',
                        }
                    ]
                },
                'skills': {'items': ['Python', 'Django', 'React', 'TypeScript', 'PostgreSQL', 'Docker', 'Redis', 'AWS']},
                'projects': {
                    'items': [
                        {
                            'title': 'Sha8alny Platform',
                            'description': 'AI-powered career development platform with skill assessment and personalized roadmaps.',
                            'technologies': ['Django', 'React', 'Gemma AI', 'ChromaDB'],
                        }
                    ]
                },
                'certifications': {
                    'items': [
                        {'name': 'AWS Cloud Practitioner', 'issuer': 'Amazon', 'date': '2023'},
                    ]
                },
                'languages': {
                    'items': [
                        {'name': 'Arabic', 'proficiency': 'Native'},
                        {'name': 'English', 'proficiency': 'Fluent'},
                    ]
                },
            },
            {
                'title': 'Data Science Resume',
                'template_name': 'classic',
                'is_primary': False,
                'personal_info': {
                    'name': 'Ahmed Mohamed',
                    'email': 'ahmed@example.com',
                    'summary': 'Data science enthusiast with experience in machine learning and NLP.',
                },
                'skills': {'items': ['Python', 'pandas', 'scikit-learn', 'TensorFlow', 'SQL', 'Tableau']},
                'education': {
                    'items': [
                        {'degree': 'B.Sc. Computer Science', 'institution': 'Cairo University', 'graduation_date': '2022'}
                    ]
                },
            },
        ]

        for data in resumes:
            Resume.objects.create(user=user, **data)

        self.stdout.write(self.style.SUCCESS(f'Created {len(resumes)} sample resumes'))
