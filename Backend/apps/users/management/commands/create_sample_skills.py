"""
Management command to create sample skills data for testing.

Usage: python manage.py create_sample_skills
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.users.models import Skill


class Command(BaseCommand):
    help = 'Create sample skills data for testing'

    def handle(self, *args, **kwargs):
        """Create sample skills."""
        skills_data = [
            # Technical Skills
            {'name': 'Python', 'category': 'technical', 'popularity_score': 95},
            {'name': 'JavaScript', 'category': 'technical', 'popularity_score': 92},
            {'name': 'Django', 'category': 'technical', 'popularity_score': 85},
            {'name': 'React', 'category': 'technical', 'popularity_score': 90},
            {'name': 'PostgreSQL', 'category': 'technical', 'popularity_score': 80},
            {'name': 'Docker', 'category': 'technical', 'popularity_score': 88},
            {'name': 'Git', 'category': 'technical', 'popularity_score': 100},
            {'name': 'REST APIs', 'category': 'technical', 'popularity_score': 93},
            {'name': 'AWS', 'category': 'technical', 'popularity_score': 87},
            {'name': 'Node.js', 'category': 'technical', 'popularity_score': 89},

            # Data Skills
            {'name': 'SQL', 'category': 'data', 'popularity_score': 95},
            {'name': 'Data Analysis', 'category': 'data', 'popularity_score': 85},
            {'name': 'Machine Learning', 'category': 'data', 'popularity_score': 82},
            {'name': 'Pandas', 'category': 'data', 'popularity_score': 78},
            {'name': 'NumPy', 'category': 'data', 'popularity_score': 75},

            # Soft Skills
            {'name': 'Communication', 'category': 'soft', 'popularity_score': 100},
            {'name': 'Problem Solving', 'category': 'soft', 'popularity_score': 98},
            {'name': 'Teamwork', 'category': 'soft', 'popularity_score': 97},
            {'name': 'Leadership', 'category': 'soft', 'popularity_score': 90},
            {'name': 'Time Management', 'category': 'soft', 'popularity_score': 92},

            # Business Skills
            {'name': 'Project Management', 'category': 'business', 'popularity_score': 88},
            {'name': 'Agile', 'category': 'business', 'popularity_score': 85},
            {'name': 'Business Analysis', 'category': 'business', 'popularity_score': 80},

            # Design Skills
            {'name': 'UI/UX Design', 'category': 'design', 'popularity_score': 87},
            {'name': 'Figma', 'category': 'design', 'popularity_score': 85},
            {'name': 'Adobe XD', 'category': 'design', 'popularity_score': 75},

            # Marketing Skills
            {'name': 'Digital Marketing', 'category': 'marketing', 'popularity_score': 82},
            {'name': 'SEO', 'category': 'marketing', 'popularity_score': 80},
            {'name': 'Content Marketing', 'category': 'marketing', 'popularity_score': 78},
        ]

        created_count = 0
        updated_count = 0

        for skill_data in skills_data:
            skill, created = Skill.objects.update_or_create(
                name=skill_data['name'],
                defaults={
                    'slug': slugify(skill_data['name']),
                    'category': skill_data['category'],
                    'popularity_score': skill_data['popularity_score'],
                    'description': f"Essential {skill_data['name']} skill for career growth",
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created skill: {skill.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated skill: {skill.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully processed {created_count + updated_count} skills '
                f'({created_count} created, {updated_count} updated)'
            )
        )
