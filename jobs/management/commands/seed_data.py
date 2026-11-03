import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import CandidateProfile, RecruiterProfile
from companies.models import Company
from jobs.models import JobCategory, Skill, Job, SavedJob
from applications.models import Application, Interview, Notification


class Command(BaseCommand):
    help = "Seed CareerConnect portal with realistic demo data, categories, users, jobs, and applications"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Starting CareerConnect data seeding..."))

        # 1. Admin Superuser
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@careerconnect.local',
                'first_name': 'Portal',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('Admin@123')
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin user (admin / Admin@123)"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Categories
        categories_data = [
            ('Software Development', 'bi-code-slash', 'Roles in software engineering, backend, frontend, and full-stack.'),
            ('Web & Cloud Technologies', 'bi-cloud', 'Web application engineering, cloud infrastructure, and DevOps.'),
            ('Data Science & AI', 'bi-cpu', 'Machine learning, data analysis, neural networks, and business intelligence.'),
            ('Design & Creative', 'bi-palette', 'UI/UX design, visual design, graphic design, and user research.'),
            ('Marketing & Content', 'bi-megaphone', 'Digital marketing, brand growth, content creation, and SEO.'),
            ('Finance & Operations', 'bi-graph-up-arrow', 'Financial analysis, corporate accounting, and operations.'),
        ]
        categories_map = {}
        for name, icon, desc in categories_data:
            cat, _ = JobCategory.objects.get_or_create(
                name=name,
                defaults={'icon': icon, 'description': desc}
            )
            categories_map[name] = cat

        # 3. Skills
        skill_names = [
            'Python', 'Django', 'JavaScript', 'React', 'HTML/CSS',
            'SQL', 'PostgreSQL', 'Docker', 'Git', 'REST APIs',
            'AWS', 'FastAPI', 'Machine Learning', 'Figma', 'UI/UX'
        ]
        skills_map = {}
        for name in skill_names:
            sk, _ = Skill.objects.get_or_create(name=name)
            skills_map[name] = sk

        # 4. Companies
        c1, _ = Company.objects.get_or_create(
            name='TechNova Solutions',
            defaults={
                'website': 'https://technova.example.com',
                'industry': 'Information Technology',
                'location': 'Bengaluru, India',
                'company_size': '201-500',
                'description': 'TechNova is a premier software engineering services provider crafting scalable cloud and web solutions for enterprise clients worldwide.',
                'is_verified': True,
            }
        )
        c2, _ = Company.objects.get_or_create(
            name='CloudScale Labs',
            defaults={
                'website': 'https://cloudscalelabs.example.com',
                'industry': 'Cloud Infrastructure & SaaS',
                'location': 'Hyderabad, India / Remote',
                'company_size': '51-200',
                'description': 'Building next-generation distributed systems, cloud computing monitoring tools, and developer platforms.',
                'is_verified': True,
            }
        )
        c3, _ = Company.objects.get_or_create(
            name='PixelCraft Studio',
            defaults={
                'website': 'https://pixelcraft.example.com',
                'industry': 'Product Design & Creative',
                'location': 'Mumbai, India',
                'company_size': '11-50',
                'description': 'Digital product studio creating intuitive, delightful user experiences for high-growth tech startups.',
                'is_verified': True,
            }
        )

        # 5. Recruiters
        rec1_user, _ = User.objects.get_or_create(
            username='recruiter_alex',
            defaults={
                'email': 'alex@technova.example.com',
                'first_name': 'Alex',
                'last_name': 'Miller',
            }
        )
        rec1_user.set_password('Recruiter@123')
        rec1_user.save()
        rec1_prof, _ = RecruiterProfile.objects.get_or_create(
            user=rec1_user,
            defaults={
                'company': c1,
                'designation': 'Lead Technical Recruiter',
                'phone': '+91 9876500001',
                'is_verified': True,
            }
        )

        rec2_user, _ = User.objects.get_or_create(
            username='recruiter_priya',
            defaults={
                'email': 'priya.sharma@cloudscale.example.com',
                'first_name': 'Priya',
                'last_name': 'Sharma',
            }
        )
        rec2_user.set_password('Recruiter@123')
        rec2_user.save()
        rec2_prof, _ = RecruiterProfile.objects.get_or_create(
            user=rec2_user,
            defaults={
                'company': c2,
                'designation': 'Talent Acquisition Partner',
                'phone': '+91 9876500002',
                'is_verified': True,
            }
        )

        # 6. Candidates
        cand1_user, _ = User.objects.get_or_create(
            username='candidate_rahul',
            defaults={
                'email': 'rahul.verma@example.com',
                'first_name': 'Rahul',
                'last_name': 'Verma',
            }
        )
        cand1_user.set_password('Candidate@123')
        cand1_user.save()
        cand1_prof, _ = CandidateProfile.objects.get_or_create(
            user=cand1_user,
            defaults={
                'headline': 'Computer Science Graduate | Aspiring Python & Django Developer',
                'phone': '+91 9123456780',
                'location': 'Bengaluru, India',
                'bio': 'Passionate software engineer with practical experience developing backend REST APIs using Django and PostgreSQL. Eager to contribute to high-impact products.',
                'education': 'B.Tech in Computer Science & Engineering (2022 - 2026)\nNational Institute of Technology\nCGPA: 8.8 / 10',
                'experience': 'Software Intern at CodeCraft Technologies (Jun 2025 - Aug 2025)\n- Built user authentication and caching layers for an internal portal.\n- Wrote comprehensive unit tests achieving 85% coverage.',
                'projects': '1. CareerConnect Job Portal: Full stack Django web portal with role-based access.\n2. TaskFlow API: High-performance task scheduler built with FastAPI and Redis.',
                'portfolio_url': 'https://rahulverma.dev',
                'github_url': 'https://github.com/rahulverma-dev',
                'linkedin_url': 'https://linkedin.com/in/rahulverma-dev',
            }
        )
        cand1_prof.skills.set([
            skills_map['Python'], skills_map['Django'], skills_map['REST APIs'],
            skills_map['SQL'], skills_map['Git'], skills_map['HTML/CSS']
        ])

        cand2_user, _ = User.objects.get_or_create(
            username='candidate_ananya',
            defaults={
                'email': 'ananya.sen@example.com',
                'first_name': 'Ananya',
                'last_name': 'Sen',
            }
        )
        cand2_user.set_password('Candidate@123')
        cand2_user.save()
        cand2_prof, _ = CandidateProfile.objects.get_or_create(
            user=cand2_user,
            defaults={
                'headline': 'Frontend & Full-Stack Developer | React & Python Enthusiast',
                'phone': '+91 9123456781',
                'location': 'Pune, India',
                'bio': 'Passionate developer crafting responsive interfaces with React, JavaScript, and integrating with robust Django backends.',
                'education': 'B.E. in Information Technology (2021 - 2025)\nPune University\nCGPA: 9.1 / 10',
                'experience': 'Frontend Developer Intern at WebFlow Solutions (Jan 2025 - May 2025)\n- Developed interactive dashboards in React with Bootstrap.\n- Connected 20+ REST API endpoints.',
                'projects': '1. React Dev Portfolio\n2. Real-time Chat App with WebSockets',
                'github_url': 'https://github.com/ananya-sen',
            }
        )
        cand2_prof.skills.set([
            skills_map['JavaScript'], skills_map['React'], skills_map['Python'],
            skills_map['HTML/CSS'], skills_map['Git']
        ])

        # 7. Job Listings
        today = timezone.now().date()
        j1, _ = Job.objects.get_or_create(
            recruiter=rec1_user,
            company=c1,
            title='Junior Django Backend Developer',
            defaults={
                'category': categories_map['Software Development'],
                'job_type': 'Full-time',
                'work_mode': 'Hybrid',
                'experience_level': 'Junior',
                'location': 'Bengaluru, India',
                'salary_min': 600000,
                'salary_max': 900000,
                'salary_negotiable': False,
                'description': 'TechNova is looking for a talented Junior Django Developer to build and maintain high-quality web applications and robust REST APIs.',
                'responsibilities': '- Develop clean, modular Django applications and database models.\n- Implement secure authentication and role-based permissions.\n- Write unit and integration test suites.\n- Collaborate closely with frontend teams.',
                'requirements': '- Solid foundation in Python 3 and Django framework.\n- Understanding of relational databases (PostgreSQL/SQLite) and ORM optimization.\n- Good knowledge of Git and version control.\n- Strong problem-solving aptitude.',
                'vacancies': 2,
                'deadline': today + datetime.timedelta(days=30),
                'is_active': True,
            }
        )
        j1.skills_required.set([
            skills_map['Python'], skills_map['Django'], skills_map['REST APIs'],
            skills_map['SQL'], skills_map['Git']
        ])

        j2, _ = Job.objects.get_or_create(
            recruiter=rec2_user,
            company=c2,
            title='Cloud Software Engineering Intern',
            defaults={
                'category': categories_map['Web & Cloud Technologies'],
                'job_type': 'Internship',
                'work_mode': 'Remote',
                'experience_level': 'Fresher',
                'location': 'Remote / India',
                'salary_min': 300000,
                'salary_max': 450000,
                'salary_negotiable': False,
                'description': 'Join CloudScale Labs as an intern! Work on scalable backend architectures, Docker containerization, and cloud infrastructure automation.',
                'responsibilities': '- Assist senior engineers in building cloud automation scripts.\n- Containerize microservices using Docker.\n- Write unit tests and maintain technical documentation.',
                'requirements': '- Currently pursuing or recently graduated with a degree in CS/IT or related field.\n- Basic knowledge of Python and Linux commands.\n- Eagerness to learn cloud technologies (Docker, AWS).',
                'vacancies': 3,
                'deadline': today + datetime.timedelta(days=45),
                'is_active': True,
            }
        )
        j2.skills_required.set([
            skills_map['Python'], skills_map['Docker'], skills_map['AWS'], skills_map['Git']
        ])

        j3, _ = Job.objects.get_or_create(
            recruiter=rec1_user,
            company=c1,
            title='Full Stack Web Developer (React + Python)',
            defaults={
                'category': categories_map['Software Development'],
                'job_type': 'Full-time',
                'work_mode': 'On-site',
                'experience_level': 'Junior',
                'location': 'Bengaluru, India',
                'salary_min': 800000,
                'salary_max': 1200000,
                'salary_negotiable': False,
                'description': 'We are hiring a Full Stack Developer passionate about crafting seamless user experiences with React and building scalable Django backends.',
                'responsibilities': '- Design responsive web interfaces.\n- Build RESTful APIs and integrate backend services.\n- Optimize web application speed and performance.',
                'requirements': '- 1-3 years of full-stack web development experience.\n- Proficiency in JavaScript, React, HTML5, CSS3, and Python/Django.\n- Familiarity with CI/CD pipelines.',
                'vacancies': 1,
                'deadline': today + datetime.timedelta(days=20),
                'is_active': True,
            }
        )
        j3.skills_required.set([
            skills_map['React'], skills_map['JavaScript'], skills_map['Python'],
            skills_map['Django'], skills_map['REST APIs']
        ])

        # 8. Applications
        app1, _ = Application.objects.get_or_create(
            job=j1,
            candidate=cand1_user,
            defaults={
                'status': 'Interview Scheduled',
                'cover_letter': 'I have built multiple full-stack Django projects and have a deep interest in backend engineering at TechNova.',
                'recruiter_notes': 'Strong skill match on Python and Django. Excellent candidate for technical round.',
            }
        )

        app2, _ = Application.objects.get_or_create(
            job=j2,
            candidate=cand1_user,
            defaults={
                'status': 'Under Review',
                'cover_letter': 'Excited to learn cloud engineering and Docker containerization at CloudScale Labs.',
            }
        )

        app3, _ = Application.objects.get_or_create(
            job=j3,
            candidate=cand2_user,
            defaults={
                'status': 'Shortlisted',
                'cover_letter': 'My experience with React interfaces and Python backends makes me a great fit for this position.',
                'recruiter_notes': 'Good portfolio with clean React projects.',
            }
        )

        # 9. Interview for app1
        Interview.objects.get_or_create(
            application=app1,
            defaults={
                'scheduled_date': today + datetime.timedelta(days=3),
                'scheduled_time': '11:00:00',
                'mode': 'Online Video Call',
                'location_or_link': 'https://meet.google.com/xyz-careerconnect-demo',
                'instructions': 'Please ensure a quiet environment with a working microphone and camera. Have your code editor ready for a 30-minute Django architecture discussion.',
            }
        )

        # 10. Saved Jobs
        SavedJob.objects.get_or_create(candidate=cand1_user, job=j3)

        # 11. Notifications
        Notification.objects.get_or_create(
            recipient=cand1_user,
            title='Interview Scheduled!',
            defaults={
                'message': f"An interview for '{j1.title}' has been scheduled for {today + datetime.timedelta(days=3)} at 11:00 AM.",
                'link': f"/applications/my/",
                'is_read': False,
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo database successfully populated!"))
        self.stdout.write(self.style.SUCCESS("""
Credentials for testing:
- Superuser / Admin: admin / Admin@123
- Recruiter 1: recruiter_alex / Recruiter@123 (TechNova Solutions)
- Recruiter 2: recruiter_priya / Recruiter@123 (CloudScale Labs)
- Candidate 1: candidate_rahul / Candidate@123 (Python & Django specialist)
- Candidate 2: candidate_ananya / Candidate@123 (Full-stack developer)
        """))
