"""
Seed resume templates for all active roles.
Uses role data (title, description, responsibilities, key_skills) to generate
realistic example content for each resume template.

Run: python manage.py seed_resume_templates
"""
from django.core.management.base import BaseCommand
from pages.models import Role, ResumeTemplate


# Department-specific summary templates
SUMMARY_TEMPLATES = {
    'Marketing': (
        "Results-driven {title} with {years}+ years of experience driving measurable growth "
        "across digital marketing channels. Proven track record of developing data-driven strategies "
        "that increase brand visibility, generate qualified leads, and optimize marketing ROI. "
        "Skilled in cross-functional collaboration and translating business objectives into impactful campaigns."
    ),
    'Product': (
        "Strategic {title} with {years}+ years of experience leading product development from "
        "ideation to launch. Expert at translating customer needs into product roadmaps, driving "
        "adoption through data-informed decisions, and aligning cross-functional teams around shared "
        "outcomes. Passionate about building products that solve real problems at scale."
    ),
    'Design': (
        "Creative and user-centered {title} with {years}+ years of experience crafting intuitive "
        "digital experiences. Skilled in leading design systems, conducting user research, and "
        "translating complex requirements into elegant, accessible interfaces. Strong advocate for "
        "design thinking and evidence-based design decisions."
    ),
    'HR': (
        "People-first {title} with {years}+ years of experience building high-performing teams "
        "and driving organizational excellence. Expertise in talent acquisition, employee engagement, "
        "performance management, and HR operations. Proven ability to align people strategy with "
        "business goals in fast-paced environments."
    ),
    'Finance': (
        "Analytical {title} with {years}+ years of experience in financial planning, reporting, "
        "and strategic analysis. Proven ability to drive cost optimization, support fundraising "
        "efforts, and deliver actionable insights to executive leadership. Strong foundation in "
        "GAAP compliance, forecasting, and cross-departmental financial partnership."
    ),
    'Leadership': (
        "Visionary {title} with {years}+ years of experience scaling organizations and driving "
        "transformational growth. Track record of building high-performing teams, establishing "
        "operational excellence, and delivering sustainable revenue growth. Skilled in strategic "
        "planning, stakeholder management, and navigating complex business challenges."
    ),
}

SENIORITY_YEARS = {
    'junior': '2',
    'mid': '5',
    'senior': '8',
    'lead': '10',
    'executive': '15',
}

EXPERIENCE_TEMPLATES = {
    'Marketing': [
        {
            "title": "Senior Marketing Manager",
            "company": "TechCorp Inc.",
            "duration": "2022 — Present",
            "bullets": [
                "Led multi-channel marketing campaigns across paid media, SEO, and content marketing, increasing qualified leads by 45%",
                "Managed $1.2M annual marketing budget with consistent ROAS above 4.5x across Google Ads and Meta platforms",
                "Built and mentored a team of 4 marketing specialists, implementing OKR framework for quarterly goal setting",
                "Developed marketing automation workflows in HubSpot, reducing manual processes by 60%",
            ],
        },
        {
            "title": "Marketing Specialist",
            "company": "GrowthLab Digital",
            "duration": "2019 — 2022",
            "bullets": [
                "Executed paid acquisition campaigns across Google, Facebook, and LinkedIn generating 2,500+ leads monthly",
                "Conducted A/B testing on landing pages and email campaigns, improving conversion rates by 32%",
                "Created content strategy for blog and social channels, growing organic traffic from 15K to 65K monthly visits",
            ],
        },
    ],
    'Product': [
        {
            "title": "Senior Product Manager",
            "company": "SaaS Platform Co.",
            "duration": "2021 — Present",
            "bullets": [
                "Owned product roadmap for core platform serving 50K+ users, driving 35% increase in user retention",
                "Led discovery and delivery of 3 major features through user research, prototyping, and iterative development",
                "Collaborated with engineering, design, and data teams to define and track key product metrics (DAU, NPS, churn)",
                "Established product analytics framework using Amplitude, enabling data-driven prioritization decisions",
            ],
        },
        {
            "title": "Product Manager",
            "company": "Digital Solutions Inc.",
            "duration": "2018 — 2021",
            "bullets": [
                "Managed end-to-end product lifecycle for B2B SaaS platform with $8M ARR",
                "Conducted 100+ customer interviews to identify pain points and validate product hypotheses",
                "Reduced onboarding time by 40% through UX improvements and guided product tours",
            ],
        },
    ],
    'Design': [
        {
            "title": "Senior UX Designer",
            "company": "Design Studio Pro",
            "duration": "2021 — Present",
            "bullets": [
                "Led UX design for enterprise SaaS platform serving 200K+ users across web and mobile",
                "Established and maintained design system with 80+ components, improving design consistency by 90%",
                "Conducted usability testing with 50+ participants, driving redesign that increased task completion by 35%",
                "Mentored 3 junior designers through structured design critique and growth frameworks",
            ],
        },
        {
            "title": "UX/UI Designer",
            "company": "Creative Agency",
            "duration": "2018 — 2021",
            "bullets": [
                "Designed responsive web and mobile interfaces for 15+ client projects across fintech, healthcare, and e-commerce",
                "Created wireframes, prototypes, and high-fidelity mockups using Figma and Adobe Creative Suite",
                "Collaborated with developers to ensure pixel-perfect implementation and accessibility compliance",
            ],
        },
    ],
    'HR': [
        {
            "title": "HR Manager",
            "company": "ScaleUp Technologies",
            "duration": "2021 — Present",
            "bullets": [
                "Managed full-cycle HR operations for 300+ employee organization across 3 offices",
                "Reduced time-to-hire by 35% through process optimization and ATS implementation",
                "Designed and launched employee engagement program, improving eNPS from 25 to 62",
                "Led compensation benchmarking project resulting in competitive pay structure across all departments",
            ],
        },
        {
            "title": "HR Coordinator",
            "company": "Global Corp",
            "duration": "2018 — 2021",
            "bullets": [
                "Supported onboarding process for 150+ new hires annually, maintaining 95% satisfaction scores",
                "Administered benefits programs and managed employee records in HRIS (Workday)",
                "Coordinated training and development programs for 5 departments",
            ],
        },
    ],
    'Finance': [
        {
            "title": "Financial Analyst",
            "company": "Investment Group LLC",
            "duration": "2021 — Present",
            "bullets": [
                "Built and maintained financial models for $50M+ portfolio of investments and business units",
                "Prepared monthly financial reports and variance analysis for C-suite, identifying $2.3M in cost savings",
                "Led annual budgeting process across 8 departments, improving forecast accuracy from 85% to 94%",
                "Automated reporting workflows using Excel VBA and Power BI, saving 20 hours per month",
            ],
        },
        {
            "title": "Junior Financial Analyst",
            "company": "Consulting Partners",
            "duration": "2018 — 2021",
            "bullets": [
                "Performed financial due diligence for M&A transactions totaling $120M",
                "Created DCF and comparable company valuation models for client presentations",
                "Assisted in quarterly board reporting and investor relations materials",
            ],
        },
    ],
    'Leadership': [
        {
            "title": "VP of Operations",
            "company": "Enterprise Solutions Corp",
            "duration": "2020 — Present",
            "bullets": [
                "Directed operations across 5 departments with 120+ employees and $25M annual budget",
                "Implemented operational excellence framework resulting in 30% efficiency improvement across key processes",
                "Led organizational restructuring during 3x growth phase, maintaining employee retention above 90%",
                "Established KPI dashboards and reporting cadence for executive leadership team",
            ],
        },
        {
            "title": "Director of Strategy",
            "company": "Growth Ventures Inc.",
            "duration": "2016 — 2020",
            "bullets": [
                "Developed and executed 3-year strategic plan resulting in 150% revenue growth",
                "Led cross-functional initiative teams for market expansion into 4 new geographic regions",
                "Built strategic partnerships generating $8M in new revenue streams",
            ],
        },
    ],
}

EDUCATION_TEMPLATES = {
    'Marketing': [{"degree": "B.S. in Marketing", "school": "University of California", "year": "2018"}],
    'Product': [{"degree": "B.S. in Computer Science", "school": "Stanford University", "year": "2017"}],
    'Design': [{"degree": "B.F.A. in Graphic Design", "school": "Rhode Island School of Design", "year": "2017"}],
    'HR': [{"degree": "B.A. in Human Resources Management", "school": "University of Michigan", "year": "2017"}],
    'Finance': [{"degree": "B.S. in Finance", "school": "New York University", "year": "2017"}, {"degree": "CFA Level II Candidate", "school": "CFA Institute", "year": "2023"}],
    'Leadership': [{"degree": "MBA", "school": "Harvard Business School", "year": "2015"}, {"degree": "B.A. in Economics", "school": "Yale University", "year": "2010"}],
}

TIPS_TEMPLATES = {
    'Marketing': [
        {"title": "Quantify campaign results", "description": "Include specific metrics like ROAS, conversion rates, and lead volume. Numbers make your impact tangible and ATS-friendly."},
        {"title": "Highlight tool proficiency", "description": "List marketing platforms (HubSpot, Google Ads, Marketo) prominently — these are common ATS filter keywords."},
        {"title": "Show business impact", "description": "Connect marketing activities to revenue outcomes. 'Generated $2M pipeline' is stronger than 'Ran email campaigns'."},
        {"title": "Include certifications", "description": "Google Ads, HubSpot, and Meta certifications signal verified expertise and are searched by recruiters."},
    ],
    'Product': [
        {"title": "Lead with outcomes", "description": "Focus on product outcomes (user growth, retention, revenue) not just features shipped."},
        {"title": "Show cross-functional leadership", "description": "Product managers are valued for their ability to align engineering, design, and business teams."},
        {"title": "Include discovery methods", "description": "Mention user research, A/B testing, and data analysis to show evidence-based decision making."},
        {"title": "Highlight technical fluency", "description": "Even non-technical PMs should show comfort with analytics tools, SQL, or API concepts."},
    ],
    'Design': [
        {"title": "Link your portfolio", "description": "Always include a portfolio URL. Recruiters expect to see your work, not just read about it."},
        {"title": "Show process, not just output", "description": "Describe your design process: research → wireframes → testing → iteration. This shows maturity."},
        {"title": "Quantify design impact", "description": "Use metrics like task completion rate, NPS improvement, or conversion lifts to prove design value."},
        {"title": "Mention design systems", "description": "Experience building or maintaining design systems signals scalable thinking and team collaboration."},
    ],
    'HR': [
        {"title": "Show strategic impact", "description": "Move beyond administrative tasks — highlight how HR initiatives drove business outcomes."},
        {"title": "Include HRIS experience", "description": "Name specific platforms (Workday, BambooHR, ADP) as these are frequently searched keywords."},
        {"title": "Quantify hiring metrics", "description": "Time-to-hire, cost-per-hire, and offer acceptance rates demonstrate measurable HR effectiveness."},
        {"title": "Highlight compliance knowledge", "description": "Mention familiarity with employment law, GDPR, or industry-specific regulations."},
    ],
    'Finance': [
        {"title": "Highlight analytical tools", "description": "Excel, SQL, Power BI, and financial modeling software are top ATS keywords for finance roles."},
        {"title": "Quantify financial impact", "description": "Include dollar amounts, percentages, and scale — '$50M portfolio', '94% forecast accuracy'."},
        {"title": "Show progression", "description": "Finance values career progression. Highlight promotions and increasing scope of responsibility."},
        {"title": "Include certifications", "description": "CPA, CFA, or FP&A certifications significantly boost your resume for senior finance roles."},
    ],
    'Leadership': [
        {"title": "Lead with scale", "description": "Open with the size of teams, budgets, and organizations you've managed to establish credibility."},
        {"title": "Show transformation", "description": "Highlight turnarounds, growth initiatives, or strategic shifts you've led — not just steady-state management."},
        {"title": "Include board-level work", "description": "Board presentations, investor relations, and governance experience differentiate executive candidates."},
        {"title": "Demonstrate people development", "description": "Show how you've built teams, developed leaders, and created organizational capability."},
    ],
}

COMMON_MISTAKES = {
    'Marketing': ["Using vague language like 'managed social media' without metrics", "Listing tools without showing results achieved with them", "Ignoring SEO keywords from the job description", "No professional summary tailored to the target role"],
    'Product': ["Focusing on features shipped instead of user/business outcomes", "Not mentioning specific methodologies (Agile, Scrum, Lean)", "Missing data and analytics skills", "No evidence of stakeholder management"],
    'Design': ["No portfolio link in the resume header", "Describing only visual design without mentioning UX process", "Missing accessibility and responsive design experience", "Not quantifying design impact with metrics"],
    'HR': ["Too focused on administrative tasks", "Not highlighting strategic initiatives", "Missing HRIS and HR tech experience", "No mention of compliance or employment law knowledge"],
    'Finance': ["No quantified financial impact or scale", "Missing key software and tools", "Not showing progression in responsibilities", "Overly technical jargon without business context"],
    'Leadership': ["Too operational, not enough strategic vision", "Missing team size and budget scale", "No mention of board or investor interactions", "Not showing measurable transformation results"],
}


class Command(BaseCommand):
    help = 'Seed resume templates for all active roles'

    def handle(self, *args, **options):
        roles = Role.objects.filter(is_active=True)
        created = 0
        updated = 0

        for role in roles:
            dept = role.department
            years = SENIORITY_YEARS.get(role.seniority_level, '5')

            summary = SUMMARY_TEMPLATES.get(dept, SUMMARY_TEMPLATES['Marketing']).format(
                title=role.title, years=years,
            )

            experience = EXPERIENCE_TEMPLATES.get(dept, EXPERIENCE_TEMPLATES['Marketing'])
            # Customize first entry title to match role
            custom_exp = []
            for i, exp in enumerate(experience):
                entry = dict(exp)
                if i == 0:
                    entry['title'] = role.title
                custom_exp.append(entry)

            skills = list(role.key_skills) if role.key_skills else []
            if not skills:
                skills = ["Communication", "Problem Solving", "Leadership", "Project Management"]

            education = EDUCATION_TEMPLATES.get(dept, EDUCATION_TEMPLATES['Marketing'])
            tips = TIPS_TEMPLATES.get(dept, TIPS_TEMPLATES['Marketing'])
            mistakes = COMMON_MISTAKES.get(dept, COMMON_MISTAKES['Marketing'])

            keywords = skills[:10]

            faqs = [
                {"q": f"How long should a {role.title} resume be?", "a": f"For most {role.title} positions, keep your resume to 1-2 pages. Senior and executive roles can justify 2 pages with extensive relevant experience."},
                {"q": f"What format is best for a {role.title} resume?", "a": "Use a clean, single-column format with standard section headers. This ensures ATS systems can parse your resume correctly. Avoid tables, columns, and graphics."},
                {"q": f"Should I include a summary on my {role.title} resume?", "a": "Yes. A 2-3 sentence professional summary at the top helps recruiters quickly understand your fit. Tailor it to each application with relevant keywords from the job description."},
                {"q": f"What skills should I highlight for {role.title} roles?", "a": f"Focus on: {', '.join(skills[:5])}. Match your skills section to the specific job description keywords for best ATS compatibility."},
                {"q": f"How do I make my {role.title} resume ATS-friendly?", "a": "Use standard section headers, include keywords from the job description, avoid images and complex formatting, and save as PDF. Our builder handles all of this automatically."},
            ]

            _, is_created = ResumeTemplate.objects.update_or_create(
                role=role,
                defaults={
                    'example_summary': summary,
                    'example_experience': custom_exp,
                    'example_skills': skills,
                    'example_education': education,
                    'resume_tips': tips,
                    'keywords_to_include': keywords,
                    'common_mistakes': mistakes,
                    'faqs': faqs,
                    'is_active': True,
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1
            self.stdout.write(f"  {'Created' if is_created else 'Updated'}: {role.title}")

        self.stdout.write(self.style.SUCCESS(f"\nDone! Created: {created}, Updated: {updated}"))
