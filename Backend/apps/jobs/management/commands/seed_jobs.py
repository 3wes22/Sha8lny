"""
Management command to seed job listings with realistic Egyptian market data.

Usage:
    python manage.py seed_jobs
    python manage.py seed_jobs --clear  # Clear existing jobs first
    python manage.py seed_jobs --count 50  # Seed 50 jobs instead of default 100
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
from decimal import Decimal
import random

from apps.jobs.models import JobPlatform, Job, JobSkill
from apps.jobs.services import JobService
from apps.users.models import Skill


class Command(BaseCommand):
    help = 'Seed job listings with realistic Egyptian market data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing jobs before seeding',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of jobs to seed (default: 100)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count = Job.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Cleared {deleted_count} existing jobs')
            )

        # Create or get job platforms
        platforms = self._create_platforms()
        self.stdout.write(
            self.style.SUCCESS(f'Created/verified {len(platforms)} job platforms')
        )

        # Get job data templates
        job_count = options['count']
        jobs_data = self._get_jobs_data(job_count)

        # Create jobs
        created_count = 0
        for job_data in jobs_data:
            platform = random.choice(platforms)
            skills = job_data.pop('skills')

            # Create job
            job = JobService.create_job(
                platform=platform,
                external_id=f"{platform.slug}_{job_data['title']}_{created_count}",
                external_url=f"{platform.website_url}/jobs/{created_count}",
                **job_data
            )

            # Add skills to job
            JobService.add_skills_to_job(job, skills, is_required=True)

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {created_count} jobs')
        )

    def _create_platforms(self):
        """Create job platforms."""
        platforms_data = [
            {
                'name': 'Wuzzuf',
                'slug': 'wuzzuf',
                'website_url': 'https://wuzzuf.net',
                'has_api': False,
                'requires_scraping': True,
                'scraping_enabled': True,
                'target_countries': ['Egypt'],
                'is_active': True,
            },
            {
                'name': 'LinkedIn Egypt',
                'slug': 'linkedin-egypt',
                'website_url': 'https://linkedin.com',
                'has_api': True,
                'api_endpoint': 'https://api.linkedin.com',
                'requires_scraping': False,
                'scraping_enabled': False,
                'target_countries': ['Egypt', 'Saudi Arabia', 'UAE'],
                'is_active': True,
            },
            {
                'name': 'Bayt',
                'slug': 'bayt',
                'website_url': 'https://bayt.com',
                'has_api': False,
                'requires_scraping': True,
                'scraping_enabled': True,
                'target_countries': ['Egypt', 'Saudi Arabia', 'UAE', 'Kuwait'],
                'is_active': True,
            },
            {
                'name': 'Forasna',
                'slug': 'forasna',
                'website_url': 'https://forasna.com',
                'has_api': False,
                'requires_scraping': True,
                'scraping_enabled': True,
                'target_countries': ['Egypt'],
                'is_active': True,
            },
        ]

        platforms = []
        for platform_data in platforms_data:
            platform, created = JobPlatform.objects.update_or_create(
                slug=platform_data['slug'],
                defaults=platform_data
            )
            platforms.append(platform)

        return platforms

    def _get_jobs_data(self, count):
        """Generate realistic job data for Egyptian market."""

        # Egyptian cities
        cities = [
            'Cairo', 'Giza', 'Alexandria', 'Maadi', 'Nasr City', 'New Cairo',
            'Sheikh Zayed', '6th of October', 'Zamalek', 'Heliopolis',
            'Smart Village', 'Mansoura', 'Tanta', 'Assiut'
        ]

        # Egyptian companies (mix of real and realistic)
        companies = [
            'Vodafone Egypt', 'Orange Egypt', 'Etisalat', 'Fawry', 'Swvl',
            'Paymob', 'Vezeeta', 'Instabug', 'Integr8', 'Bey2ollak',
            'Elmenus', 'Halan', 'Breadfast', 'MaxAB', 'Brimore',
            'TechHub Cairo', 'Digital Egypt', 'Smart Solutions', 'Code Valley',
            'Innovate IT', 'Tech Pioneers', 'Digital Minds', 'Future Tech',
            'CloudWare Egypt', 'DataCraft', 'WebMasters Egypt'
        ]

        # Job templates by career path
        job_templates = [
            # Backend Developer Jobs
            {
                'title': 'Backend Developer (Python/Django)',
                'description': 'We are looking for an experienced Backend Developer to join our team. You will be responsible for building scalable APIs, optimizing database queries, and implementing secure authentication systems.',
                'requirements': 'Strong proficiency in Python and Django. Experience with PostgreSQL, Redis, and RESTful API design. Knowledge of Docker and CI/CD pipelines.',
                'responsibilities': 'Design and implement RESTful APIs. Optimize database queries and server performance. Collaborate with frontend developers. Write comprehensive tests.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 5,
                'salary_min': Decimal('15000'),
                'salary_max': Decimal('30000'),
                'salary_period': 'monthly',
                'skills': ['Python', 'Django', 'PostgreSQL', 'REST APIs', 'Docker'],
            },
            {
                'title': 'Senior Backend Engineer (Node.js)',
                'description': 'Join our engineering team to build high-performance backend services. You will architect scalable microservices and mentor junior developers.',
                'requirements': '5+ years of experience with Node.js and Express. Strong knowledge of MongoDB, Redis, and message queues. Experience leading technical teams.',
                'responsibilities': 'Architect microservices infrastructure. Lead code reviews and mentorship. Optimize application performance. Design database schemas.',
                'job_type': 'full_time',
                'experience_level': 'senior',
                'experience_years_min': 5,
                'experience_years_max': 10,
                'salary_min': Decimal('30000'),
                'salary_max': Decimal('50000'),
                'salary_period': 'monthly',
                'skills': ['Node.js', 'Express', 'MongoDB', 'Redis', 'Microservices'],
            },
            # Frontend Developer Jobs
            {
                'title': 'Frontend Developer (React)',
                'description': 'We need a talented Frontend Developer to create beautiful, responsive user interfaces. You will work with React, TypeScript, and modern CSS frameworks.',
                'requirements': 'Proficiency in React, TypeScript, and Tailwind CSS. Experience with state management (Redux/Context). Understanding of responsive design principles.',
                'responsibilities': 'Build reusable React components. Implement responsive designs. Optimize frontend performance. Collaborate with UX designers.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 4,
                'salary_min': Decimal('12000'),
                'salary_max': Decimal('25000'),
                'salary_period': 'monthly',
                'skills': ['React', 'TypeScript', 'Tailwind CSS', 'Redux', 'JavaScript'],
            },
            {
                'title': 'Junior Frontend Developer',
                'description': 'Great opportunity for fresh graduates or junior developers to join our frontend team. Learn from experienced engineers while building production applications.',
                'requirements': 'Basic knowledge of HTML, CSS, and JavaScript. Familiarity with React or Vue.js. Passion for creating great user experiences.',
                'responsibilities': 'Implement UI components based on designs. Fix bugs and improve code quality. Learn best practices from senior developers.',
                'job_type': 'full_time',
                'experience_level': 'entry',
                'experience_years_min': 0,
                'experience_years_max': 2,
                'salary_min': Decimal('6000'),
                'salary_max': Decimal('12000'),
                'salary_period': 'monthly',
                'skills': ['HTML', 'CSS', 'JavaScript', 'React', 'Git'],
            },
            # Full Stack Developer Jobs
            {
                'title': 'Full Stack Developer (MERN)',
                'description': 'Looking for a versatile Full Stack Developer to work on both frontend and backend. You will build end-to-end features using the MERN stack.',
                'requirements': 'Experience with MongoDB, Express, React, and Node.js. Ability to design APIs and implement frontend features. Knowledge of deployment processes.',
                'responsibilities': 'Develop full-stack features. Design and implement RESTful APIs. Build responsive user interfaces. Deploy applications to production.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 3,
                'experience_years_max': 6,
                'salary_min': Decimal('18000'),
                'salary_max': Decimal('35000'),
                'salary_period': 'monthly',
                'skills': ['React', 'Node.js', 'MongoDB', 'Express', 'JavaScript'],
            },
            # Data Science Jobs
            {
                'title': 'Data Scientist',
                'description': 'Join our data team to build machine learning models and derive insights from large datasets. You will work on predictive analytics and data visualization.',
                'requirements': 'Strong Python skills with pandas, NumPy, and scikit-learn. Experience with SQL and data visualization. Knowledge of machine learning algorithms.',
                'responsibilities': 'Build predictive models. Analyze large datasets. Create data visualizations. Collaborate with business stakeholders.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 5,
                'salary_min': Decimal('20000'),
                'salary_max': Decimal('40000'),
                'salary_period': 'monthly',
                'skills': ['Python', 'Machine Learning', 'pandas', 'SQL', 'TensorFlow'],
            },
            {
                'title': 'ML Engineer',
                'description': 'We are seeking an ML Engineer to deploy machine learning models to production. You will optimize model performance and build ML pipelines.',
                'requirements': '3+ years experience with Python and ML frameworks. Experience deploying models to production. Knowledge of Docker and Kubernetes.',
                'responsibilities': 'Deploy ML models to production. Build data pipelines. Optimize model performance. Monitor model metrics.',
                'job_type': 'full_time',
                'experience_level': 'senior',
                'experience_years_min': 3,
                'experience_years_max': 7,
                'salary_min': Decimal('25000'),
                'salary_max': Decimal('45000'),
                'salary_period': 'monthly',
                'skills': ['Python', 'Machine Learning', 'Docker', 'Kubernetes', 'MLOps'],
            },
            # DevOps Jobs
            {
                'title': 'DevOps Engineer',
                'description': 'Looking for a DevOps Engineer to manage our infrastructure and automate deployment processes. You will work with AWS, Docker, and Kubernetes.',
                'requirements': 'Experience with AWS/Azure. Strong knowledge of Docker and Kubernetes. Proficiency in CI/CD tools (Jenkins, GitLab CI). Shell scripting skills.',
                'responsibilities': 'Manage cloud infrastructure. Automate deployment pipelines. Monitor system performance. Implement security best practices.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 3,
                'experience_years_max': 6,
                'salary_min': Decimal('22000'),
                'salary_max': Decimal('40000'),
                'salary_period': 'monthly',
                'skills': ['AWS', 'Docker', 'Kubernetes', 'CI/CD', 'Linux'],
            },
            # Mobile Developer Jobs
            {
                'title': 'Android Developer (Kotlin)',
                'description': 'Join our mobile team to build native Android applications. You will work with Kotlin, Jetpack Compose, and modern Android architecture.',
                'requirements': 'Strong Kotlin experience. Knowledge of Android SDK and Jetpack libraries. Experience with MVVM/Clean Architecture. Understanding of Material Design.',
                'responsibilities': 'Develop Android applications. Implement Material Design guidelines. Optimize app performance. Write unit and UI tests.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 5,
                'salary_min': Decimal('15000'),
                'salary_max': Decimal('30000'),
                'salary_period': 'monthly',
                'skills': ['Kotlin', 'Android', 'Jetpack Compose', 'MVVM', 'REST APIs'],
            },
            {
                'title': 'Flutter Developer',
                'description': 'We need a Flutter Developer to build cross-platform mobile applications. You will create beautiful, performant apps for iOS and Android.',
                'requirements': 'Experience with Flutter and Dart. Knowledge of state management (Provider/Riverpod/Bloc). Understanding of mobile app lifecycle.',
                'responsibilities': 'Build cross-platform mobile apps. Implement responsive UI designs. Integrate with backend APIs. Optimize app performance.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 4,
                'salary_min': Decimal('14000'),
                'salary_max': Decimal('28000'),
                'salary_period': 'monthly',
                'skills': ['Flutter', 'Dart', 'Mobile Development', 'REST APIs', 'State Management'],
            },
            # UI/UX Designer Jobs
            {
                'title': 'UI/UX Designer',
                'description': 'Looking for a creative UI/UX Designer to create intuitive user experiences. You will work with Figma, conduct user research, and design wireframes.',
                'requirements': 'Proficiency in Figma and Adobe XD. Strong portfolio demonstrating UX process. Understanding of user-centered design principles.',
                'responsibilities': 'Create wireframes and prototypes. Conduct user research. Design user interfaces. Collaborate with developers.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 5,
                'salary_min': Decimal('10000'),
                'salary_max': Decimal('22000'),
                'salary_period': 'monthly',
                'skills': ['Figma', 'UI Design', 'UX Research', 'Prototyping', 'Adobe XD'],
            },
            # QA Jobs
            {
                'title': 'QA Engineer (Manual & Automation)',
                'description': 'We need a QA Engineer to ensure our software quality. You will write test cases, perform manual testing, and build automation frameworks.',
                'requirements': 'Experience with manual and automated testing. Knowledge of Selenium or Cypress. Understanding of QA methodologies.',
                'responsibilities': 'Write and execute test cases. Build automation frameworks. Report and track bugs. Collaborate with development team.',
                'job_type': 'full_time',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 4,
                'salary_min': Decimal('12000'),
                'salary_max': Decimal('22000'),
                'salary_period': 'monthly',
                'skills': ['QA Testing', 'Selenium', 'Test Automation', 'Cypress', 'API Testing'],
            },
            # Internship Jobs
            {
                'title': 'Software Engineering Intern',
                'description': 'Summer internship program for computer science students. Work on real projects, learn from experienced engineers, and build your portfolio.',
                'requirements': 'Currently enrolled in Computer Science or related field. Basic programming knowledge. Passion for learning.',
                'responsibilities': 'Work on assigned projects. Learn development best practices. Participate in code reviews. Attend team meetings.',
                'job_type': 'internship',
                'experience_level': 'entry',
                'experience_years_min': 0,
                'experience_years_max': 0,
                'salary_min': Decimal('3000'),
                'salary_max': Decimal('5000'),
                'salary_period': 'monthly',
                'skills': ['Programming', 'Git', 'Problem Solving', 'Communication'],
            },
            # Contract/Freelance Jobs
            {
                'title': 'Freelance WordPress Developer',
                'description': 'Looking for a WordPress developer for short-term contract work. Build custom themes and plugins.',
                'requirements': 'Strong WordPress experience. PHP and MySQL knowledge. Experience with theme development.',
                'responsibilities': 'Develop WordPress themes. Build custom plugins. Customize existing themes. Fix bugs and issues.',
                'job_type': 'freelance',
                'experience_level': 'mid',
                'experience_years_min': 2,
                'experience_years_max': 5,
                'salary_min': Decimal('500'),
                'salary_max': Decimal('1500'),
                'salary_period': 'hourly',
                'skills': ['WordPress', 'PHP', 'MySQL', 'CSS', 'JavaScript'],
            },
        ]

        # Generate jobs
        jobs = []
        for i in range(count):
            template = random.choice(job_templates).copy()

            # Randomize location
            location_city = random.choice(cities)
            is_remote = random.choice([True, False, False, False])  # 25% remote

            if is_remote:
                remote_type = random.choice(['fully_remote', 'hybrid'])
            else:
                remote_type = 'on_site'

            # Random salary variation (+/- 20%)
            salary_variation = random.uniform(0.8, 1.2)
            salary_min = template['salary_min'] * Decimal(str(salary_variation))
            salary_max = template['salary_max'] * Decimal(str(salary_variation))

            # Posted date (within last 30 days)
            days_ago = random.randint(1, 30)
            posted_date = (timezone.now() - timedelta(days=days_ago)).date()

            # Application deadline (30-90 days from posting)
            deadline_days = random.randint(30, 90)
            application_deadline = (timezone.now() + timedelta(days=deadline_days)).date()

            job = {
                'title': template['title'],
                'company_name': random.choice(companies),
                'description': template['description'],
                'requirements': template['requirements'],
                'responsibilities': template['responsibilities'],
                'location_city': location_city,
                'location_country': 'Egypt',
                'is_remote': is_remote,
                'remote_type': remote_type,
                'job_type': template['job_type'],
                'experience_level': template['experience_level'],
                'experience_years_min': template['experience_years_min'],
                'experience_years_max': template['experience_years_max'],
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': 'EGP',
                'salary_period': template['salary_period'],
                'salary_disclosed': random.choice([True, False]),
                'posted_date': posted_date,
                'application_deadline': application_deadline,
                'is_active': True,
                'skills': template['skills'],
            }

            jobs.append(job)

        return jobs
