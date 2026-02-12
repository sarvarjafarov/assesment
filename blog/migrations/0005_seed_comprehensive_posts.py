from django.db import migrations
from django.utils import timezone
from datetime import timedelta


def seed_categories_and_posts(apps, schema_editor):
    BlogCategory = apps.get_model("blog", "BlogCategory")
    BlogPost = apps.get_model("blog", "BlogPost")

    # ── Categories ──
    categories = {}
    category_data = [
        {
            "name": "Hiring Strategy",
            "slug": "hiring-strategy",
            "description": "Expert advice on building structured, bias-free hiring processes that predict on-the-job success.",
            "order": 1,
        },
        {
            "name": "Assessment Guides",
            "slug": "assessment-guides",
            "description": "Deep dives into each assessment type—what it measures, how to use it, and how to interpret results.",
            "order": 2,
        },
        {
            "name": "Product & Platform",
            "slug": "product-platform",
            "description": "Feature updates, integration guides, and tips for getting the most out of Evalon.",
            "order": 3,
        },
        {
            "name": "Industry Insights",
            "slug": "industry-insights",
            "description": "Data-backed trends in talent acquisition, workforce planning, and people analytics.",
            "order": 4,
        },
    ]
    for cat in category_data:
        obj, _ = BlogCategory.objects.update_or_create(
            slug=cat["slug"], defaults=cat
        )
        categories[cat["slug"]] = obj

    now = timezone.now()

    # ── Posts ──
    posts = [
        # ── 1. Structured Hiring (covers homepage "How it works") ──
        {
            "title": "The Complete Guide to Structured Hiring in 2026",
            "slug": "complete-guide-structured-hiring",
            "hero_image": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Hiring Strategy",
            "pill_style": "accent",
            "excerpt": "Structured hiring removes guesswork from your process. Learn how to design consistent interview loops, calibrate scorecards, and reduce bias—step by step.",
            "body": (
                "## Why structured hiring matters\n\n"
                "Research from Google's People Operations team and the National Bureau of Economic Research consistently shows that structured interviews predict job performance **two to three times better** than unstructured conversations. Yet most companies still rely on gut-feel panel interviews.\n\n"
                "Structured hiring means every candidate sees the same questions, evaluated against the same rubric, by calibrated interviewers. The result? Faster decisions, fairer outcomes, and better hires.\n\n"
                "## The four pillars of a structured process\n\n"
                "### 1. Define the role before you source\n"
                "Write a job scorecard—not a wish list. A scorecard captures 4–6 measurable outcomes the person must deliver in their first year. These outcomes drive every downstream decision: which assessment to send, which interview questions to ask, and how to calibrate the debrief.\n\n"
                "### 2. Use validated assessments early\n"
                "Assessments should come *before* live interviews, not after. When you screen candidates with a standardized skills test first, you enter the interview with data. You know where to probe and where to skip. Evalon's six assessment banks—Marketing, Product, Behavioral, UX/UI, HR, and Finance—are designed for exactly this stage.\n\n"
                "### 3. Calibrate your interview panel\n"
                "Before anyone sits across from a candidate, align on what \"great\" looks like. Share the scorecard. Walk through sample answers at each score level (1–4). Disagreement in calibration is healthy—disagreement in a live debrief is expensive.\n\n"
                "### 4. Debrief with data, not opinions\n"
                "Collect written feedback before the group discussion. Each interviewer scores independently, then you discuss. This prevents anchoring bias—the loudest voice in the room shouldn't set the bar.\n\n"
                "## How Evalon fits in\n\n"
                "Evalon's platform automates the first two pillars. You create a project, select the right assessment bank, invite candidates by email, and receive scored profiles within 48 hours. From there, your panel enters the interview stage with a head start.\n\n"
                "## Quick-start checklist\n\n"
                "- [ ] Write a job scorecard with 4–6 measurable outcomes\n"
                "- [ ] Choose the matching Evalon assessment bank\n"
                "- [ ] Send assessments before scheduling interviews\n"
                "- [ ] Calibrate interviewers on the scorecard rubric\n"
                "- [ ] Collect independent written feedback before debriefing\n"
                "- [ ] Make a data-driven hiring decision within 48 hours of final interview\n\n"
                "Structured hiring isn't more work—it's *less rework*. Companies that adopt this approach see up to 40% lower attrition in the first year."
            ),
            "author_name": "Maya Thompson",
            "author_title": "VP People, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=2),
            "meta_title": "Complete Guide to Structured Hiring in 2026 | Evalon",
            "meta_description": "Learn how structured hiring reduces bias, predicts performance, and speeds up decisions. Step-by-step guide with a free checklist.",
            "meta_keywords": "structured hiring, structured interviews, hiring process, reduce bias hiring, interview scorecard, hiring best practices",
            "meta_image": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
            "is_featured": True,
            "category_slug": "hiring-strategy",
        },
        # ── 2. Marketing Assessment deep dive ──
        {
            "title": "How to Evaluate Marketing Talent: A Data-Driven Approach",
            "slug": "evaluate-marketing-talent-data-driven",
            "hero_image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Marketing",
            "pill_style": "neutral",
            "excerpt": "Resumes don't reveal whether a marketer can actually run a profitable paid campaign. Here's how skills-based assessments close the gap between credentials and capability.",
            "body": (
                "## The problem with marketing hiring today\n\n"
                "Marketing is one of the hardest functions to hire for because the role titles are vague. A \"Growth Manager\" at a 50-person startup and a \"Growth Manager\" at a Fortune 500 company do completely different work. Resumes list tools (Google Ads, HubSpot, Mixpanel) but tell you nothing about strategic thinking.\n\n"
                "## What Evalon's Marketing Assessment measures\n\n"
                "Our marketing assessment bank covers three core competencies:\n\n"
                "### Paid media strategy\n"
                "Candidates are given a realistic budget, target CPA, and audience segment. They must allocate spend across channels, justify their media mix, and forecast results. This reveals whether they think in terms of *unit economics* or just \"more impressions.\"\n\n"
                "### SEO and content strategy\n"
                "We present a content audit scenario—pages with declining traffic, keyword cannibalization, and technical debt. Candidates prioritize fixes and explain their reasoning. Strong marketers distinguish between quick wins (fixing title tags) and long-term plays (topical authority).\n\n"
                "### Analytics and attribution\n"
                "Given a multi-touch conversion path, candidates must identify which channels deserve credit, recommend an attribution model, and flag data quality issues. This separates the \"dashboard watchers\" from the analysts who drive decisions.\n\n"
                "## Best practices for marketing hiring managers\n\n"
                "1. **Send the assessment before the phone screen.** You'll immediately know who to fast-track.\n"
                "2. **Customize the scoring weights.** If you're hiring for a performance marketing role, weight paid media at 50%. For a content lead, weight SEO higher.\n"
                "3. **Use the results in the interview.** Ask candidates to walk through their assessment answers live. You'll learn how they think under pressure.\n"
                "4. **Benchmark against your team.** Have your top performers take the same assessment. This calibrates your expectations to reality.\n\n"
                "## Results from early adopters\n\n"
                "Companies using Evalon's marketing assessment report **35% faster time-to-hire** and **2.1x higher hiring manager satisfaction** compared to portfolio-only screening. The assessment doesn't replace the interview—it makes the interview dramatically more productive."
            ),
            "author_name": "Ibrahim Solak",
            "author_title": "Head of Growth, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=5),
            "meta_title": "How to Evaluate Marketing Talent with Skills Assessments | Evalon",
            "meta_description": "Go beyond resumes. Learn how data-driven marketing assessments measure paid media, SEO, and analytics skills to predict on-the-job performance.",
            "meta_keywords": "marketing assessment, evaluate marketing talent, marketing hiring, paid media test, SEO assessment, marketing skills test",
            "meta_image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "assessment-guides",
        },
        # ── 3. Product Management Assessment ──
        {
            "title": "Hiring Product Managers Who Ship: Beyond the Case Interview",
            "slug": "hiring-product-managers-beyond-case-interview",
            "hero_image": "https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Product",
            "pill_style": "success",
            "excerpt": "Case interviews test presentation skills, not product sense. Here's how to assess the competencies that actually predict PM success—prioritization, execution, and stakeholder alignment.",
            "body": (
                "## Why traditional PM interviews fail\n\n"
                "The classic PM case study—\"How would you improve Google Maps?\"—tests a candidate's ability to brainstorm features on a whiteboard. But the day-to-day reality of product management is messier: triaging bugs, negotiating scope with engineering, interpreting ambiguous metrics, and saying no to stakeholders.\n\n"
                "## The three competencies that matter\n\n"
                "### Prioritization under constraints\n"
                "Great PMs don't just list ideas—they rank them. Evalon's product assessment presents candidates with a backlog of 12 feature requests, a fixed engineering team, and a quarterly deadline. They must ship the highest-impact subset and explain what they cut and why.\n\n"
                "### Execution and technical communication\n"
                "We give candidates a real PRD (product requirements document) with intentional gaps: missing edge cases, undefined error states, ambiguous acceptance criteria. Their job is to spot the gaps and rewrite the spec. This is what PMs do every day.\n\n"
                "### Stakeholder alignment\n"
                "In a simulated scenario, the VP of Sales wants a feature that conflicts with the product roadmap. Candidates must craft a response that acknowledges the business need while protecting long-term strategy. We evaluate empathy, clarity, and backbone.\n\n"
                "## How to integrate the PM assessment into your loop\n\n"
                "1. **Send the assessment after the recruiter screen** — before the hiring manager call.\n"
                "2. **Review the scorecard together** with your engineering counterpart. PMs must earn trust from both sides.\n"
                "3. **Use the prioritization exercise as a live discussion** in the on-site. Ask candidates to defend their choices and adapt to new information.\n"
                "4. **Weight execution over ideation.** Anyone can brainstorm features. Shipping is the hard part.\n\n"
                "## What we've learned\n\n"
                "After analyzing over 1,200 PM assessment sessions, we found that candidates who score in the top quartile on execution receive offers **2.4x more often** than those who score highest on ideation alone. The best PMs are *editors*, not *authors*—they refine, cut, and clarify."
            ),
            "author_name": "Anika Patel",
            "author_title": "Director of Product, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=8),
            "meta_title": "How to Hire Product Managers: Skills Assessment Guide | Evalon",
            "meta_description": "Move beyond case interviews. Learn how to assess PM prioritization, execution, and stakeholder skills with structured product management assessments.",
            "meta_keywords": "product manager assessment, PM hiring, product management test, hire product managers, product sense, PM interview",
            "meta_image": "https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "assessment-guides",
        },
        # ── 4. UX/UI Design Assessment ──
        {
            "title": "Assessing UX/UI Designers: Portfolio Reviews Aren't Enough",
            "slug": "assessing-ux-ui-designers-beyond-portfolios",
            "hero_image": "https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "UX/UI Design",
            "pill_style": "accent",
            "excerpt": "A beautiful portfolio can hide weak research skills. Learn how to evaluate the full design spectrum—user research, interaction design, visual craft, and accessibility awareness.",
            "body": (
                "## The portfolio problem\n\n"
                "Portfolios are curated highlight reels. They show polished final deliverables but reveal nothing about how the designer got there. Did they run user research? Did they iterate based on data? Did they consider accessibility? You can't tell from a Dribbble shot.\n\n"
                "## What Evalon's UX/UI assessment covers\n\n"
                "### User research and problem framing\n"
                "Candidates receive a scenario: declining engagement in a SaaS onboarding flow. They must write a research plan—what questions to ask, which methods to use (interviews, surveys, usability tests), and how they'd recruit participants. This reveals whether they start with users or start with pixels.\n\n"
                "### Interaction design\n"
                "We present a wireframe with usability issues: confusing navigation, inconsistent patterns, missing feedback states. Candidates identify the problems, explain the cognitive principles at play (Fitts's Law, recognition over recall, progressive disclosure), and propose solutions.\n\n"
                "### Visual design and systems thinking\n"
                "Given a style guide with inconsistencies (mismatched spacing, orphaned components, color contrast failures), candidates audit the system and recommend fixes. Strong designers think in *systems*, not individual screens.\n\n"
                "### Accessibility\n"
                "Every designer should understand WCAG basics. We test color contrast awareness, screen reader considerations, keyboard navigation, and alt text strategy. This isn't a bonus—it's a baseline.\n\n"
                "## Tips for design hiring managers\n\n"
                "- **Pair the assessment with a portfolio review.** Use the assessment to evaluate process; use the portfolio to evaluate craft.\n"
                "- **Don't time-pressure creative work.** Our design assessment gives candidates 72 hours to submit. This reflects the real pace of thoughtful design work.\n"
                "- **Involve engineering in the review.** Designers who produce dev-ready specs are more valuable. Ask an engineer to score the interaction design section.\n"
                "- **Look for T-shaped skills.** The best designers go deep in one area (research, visual, interaction) while maintaining literacy across all three.\n\n"
                "## The accessibility imperative\n\n"
                "With the European Accessibility Act taking effect in 2025 and ADA lawsuits rising year over year, accessibility skills aren't optional. Our assessment gives you a clear signal on whether a candidate treats accessibility as an afterthought or a design principle."
            ),
            "author_name": "Lena Ortiz",
            "author_title": "Director of Platform, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=12),
            "meta_title": "How to Assess UX/UI Designers Beyond Portfolios | Evalon",
            "meta_description": "Portfolios don't tell the full story. Learn how to evaluate UX research, interaction design, visual systems, and accessibility with structured design assessments.",
            "meta_keywords": "UX assessment, UI design test, UX designer hiring, design skills assessment, UX research evaluation, accessibility hiring",
            "meta_image": "https://images.unsplash.com/photo-1586717791821-3f44a563fa4c?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "assessment-guides",
        },
        # ── 5. Behavioral Assessment deep dive ──
        {
            "title": "Behavioral Assessments: Measuring the Traits That Predict Team Success",
            "slug": "behavioral-assessments-predict-team-success",
            "hero_image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Behavioral",
            "pill_style": "neutral",
            "excerpt": "Technical skills get candidates in the door. Behavioral traits determine whether they stay, grow, and elevate the people around them. Here's how to measure what matters.",
            "body": (
                "## Skills vs. traits: the retention equation\n\n"
                "A study by Leadership IQ found that 46% of new hires fail within 18 months—and 89% of those failures are due to attitudinal issues, not technical skill gaps. Coachability, collaboration, emotional regulation, and ownership are the traits that predict long-term success.\n\n"
                "## What Evalon's Behavioral Assessment measures\n\n"
                "Our behavioral bank is grounded in industrial-organizational psychology and measures five core dimensions:\n\n"
                "### 1. Collaboration and teamwork\n"
                "How does the candidate navigate disagreements? Do they default to hierarchy or seek consensus? We present workplace scenarios—cross-functional conflicts, competing priorities, unclear ownership—and evaluate how candidates balance assertiveness with empathy.\n\n"
                "### 2. Growth mindset and coachability\n"
                "We present candidates with critical feedback on a hypothetical project. Their response reveals whether they internalize and adapt or deflect and defend. Companies with high-coachability teams iterate faster and ship more reliably.\n\n"
                "### 3. Ownership and accountability\n"
                "In a scenario where a project misses its deadline, candidates must explain what happened and what they'd do differently. We're not looking for blame—we're looking for *causal reasoning* and proactive recovery.\n\n"
                "### 4. Communication clarity\n"
                "Candidates summarize a complex technical topic for a non-technical audience. This tests whether they adjust their communication style to the listener—a critical skill in cross-functional organizations.\n\n"
                "### 5. Adaptability under ambiguity\n"
                "When priorities shift mid-sprint, how does the candidate respond? We simulate ambiguous situations—changing requirements, incomplete information, competing stakeholders—and evaluate comfort with uncertainty.\n\n"
                "## Using behavioral data in your hiring loop\n\n"
                "- **Combine behavioral and skills assessments.** A candidate with strong technical skills and weak collaboration is a very different hire than the reverse.\n"
                "- **Share the behavioral profile with interviewers.** They can probe deeper on areas of concern rather than asking generic questions.\n"
                "- **Use it for team composition.** If your current team is high on execution but low on strategic thinking, weight those dimensions accordingly.\n"
                "- **Revisit at the 90-day check-in.** Compare the assessment predictions to on-the-job observations. This calibrates your process over time.\n\n"
                "## The science behind it\n\n"
                "Evalon's behavioral items are adapted from validated I-O psychology frameworks. Each scenario is piloted with a norming sample, and items that don't discriminate between high and low performers are retired. The goal isn't to test personality—it's to predict *behavior in context*."
            ),
            "author_name": "Maya Thompson",
            "author_title": "VP People, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=15),
            "meta_title": "Behavioral Assessments That Predict Team Success | Evalon",
            "meta_description": "89% of new-hire failures are behavioral, not technical. Learn how psychometric assessments measure collaboration, coachability, and ownership to predict retention.",
            "meta_keywords": "behavioral assessment, psychometric test, soft skills assessment, team success predictors, coachability, collaboration hiring",
            "meta_image": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "assessment-guides",
        },
        # ── 6. HR Assessment ──
        {
            "title": "Hiring HR Professionals: Assessing the People Who Assess People",
            "slug": "hiring-hr-professionals-assessment",
            "hero_image": "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "HR",
            "pill_style": "success",
            "excerpt": "HR teams are the architects of your hiring process. When you hire an HR professional, you need to evaluate their knowledge of employment law, talent strategy, and employee relations—not just their interview presence.",
            "body": (
                "## The irony of HR hiring\n\n"
                "HR professionals design hiring processes for everyone else—but who designs the process for hiring *them*? Too often, HR hires are evaluated on rapport and cultural fit alone. That's a recipe for compliance risk and strategic drift.\n\n"
                "## What Evalon's HR Assessment covers\n\n"
                "### Talent acquisition strategy\n"
                "Candidates design a recruiting plan for a hard-to-fill role. We evaluate their understanding of sourcing channels, employer branding, candidate experience, and time-to-fill optimization. The best HR professionals think like marketers when it comes to talent.\n\n"
                "### Employee relations and conflict resolution\n"
                "We present a nuanced workplace conflict—a manager accused of favoritism, an employee requesting accommodation, a team dispute over remote work policies. Candidates must balance empathy, policy, and legal compliance. There are no easy answers, and that's the point.\n\n"
                "### Compliance and employment law\n"
                "Scenario-based questions test knowledge of anti-discrimination law, wage and hour regulations, leave policies (FMLA, ADA), and documentation requirements. This isn't a bar exam—it's practical, applied knowledge that prevents lawsuits.\n\n"
                "### People analytics\n"
                "Given a dataset of turnover, engagement survey results, and compensation data, candidates must identify patterns and recommend interventions. Data literacy is no longer optional for HR leaders.\n\n"
                "## Building your HR hiring loop\n\n"
                "1. **Use the HR assessment as a first-round filter.** Compliance knowledge is non-negotiable. Screen for it early.\n"
                "2. **Pair with a behavioral assessment.** HR professionals need exceptional emotional intelligence. Use the behavioral bank to measure empathy and communication.\n"
                "3. **Include a cross-functional interviewer.** Have a business leader evaluate whether the HR candidate understands commercial context—not just policy.\n"
                "4. **Ask for a 90-day plan.** Strong HR hires can articulate their onboarding priorities before they start.\n\n"
                "## Why it matters now\n\n"
                "With hybrid work, AI-driven recruiting, and evolving labor laws, HR is more complex than ever. The HR professionals you hire today will shape your organization's ability to attract, retain, and develop talent for years to come. Get the hire right."
            ),
            "author_name": "Maya Thompson",
            "author_title": "VP People, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=18),
            "meta_title": "How to Hire HR Professionals with Skills Assessments | Evalon",
            "meta_description": "Evaluate HR candidates on compliance knowledge, talent strategy, conflict resolution, and people analytics—not just cultural fit. Structured HR assessment guide.",
            "meta_keywords": "HR assessment, hire HR professionals, human resources test, talent acquisition assessment, employee relations, HR compliance",
            "meta_image": "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "assessment-guides",
        },
        # ── 7. Finance Assessment ──
        {
            "title": "Finance Manager Assessments: Testing Strategic Thinking, Not Just Spreadsheet Skills",
            "slug": "finance-manager-assessments-strategic-thinking",
            "hero_image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Finance",
            "pill_style": "accent",
            "excerpt": "Any analyst can build a DCF model. But can they advise the CEO on capital allocation under uncertainty? Here's how to assess the finance leaders your business actually needs.",
            "body": (
                "## Beyond the spreadsheet test\n\n"
                "Finance hiring has traditionally relied on technical exercises: build a three-statement model, calculate WACC, walk through a DCF. These tests confirm a baseline of technical competence but miss the skills that separate a finance *analyst* from a finance *leader*: strategic judgment, risk framing, and executive communication.\n\n"
                "## What Evalon's Finance Manager Assessment covers\n\n"
                "### Financial planning and analysis (FP&A)\n"
                "Candidates receive a company's P&L with three quarters of actuals and must build a Q4 forecast. The twist: revenue trends are ambiguous, and the CFO needs a range of scenarios (base, upside, downside). We evaluate whether candidates present a single number or a probability-weighted range with assumptions clearly stated.\n\n"
                "### Budgeting and resource allocation\n"
                "Given a fixed budget and five department heads requesting increases, candidates must allocate funds and defend their rationale. This tests whether they think in terms of *ROI per dollar* or *seniority of the requester*.\n\n"
                "### Risk management\n"
                "We present a scenario—a key customer representing 30% of revenue signals potential churn. Candidates must quantify the financial impact, propose mitigation strategies, and recommend how to communicate the risk to the board. The best answers balance transparency with calm.\n\n"
                "### Strategic finance and capital allocation\n"
                "Should the company fund a new product line with debt or equity? Candidates evaluate the trade-offs—dilution vs. interest expense, covenant restrictions, market timing—and make a recommendation with a supporting analysis. This is where finance managers earn their seat at the leadership table.\n\n"
                "## Tips for finance hiring managers\n\n"
                "- **Don't test what Excel certifications already prove.** Focus on judgment, not formulas.\n"
                "- **Evaluate communication alongside analysis.** Finance leaders present to non-finance stakeholders constantly. Can the candidate translate a waterfall chart into a board-ready narrative?\n"
                "- **Test for intellectual honesty.** The best finance candidates say \"I don't have enough data to answer this with confidence\" rather than over-engineering a false-precision model.\n"
                "- **Benchmark against your current team.** If your best FP&A analyst scores 85%, use that as your hiring bar.\n\n"
                "## The strategic finance imperative\n\n"
                "In a higher-interest-rate environment, capital allocation decisions carry more weight than ever. The finance managers you hire today need to be strategic partners, not just report generators. Evalon's assessment identifies the candidates who think like CFOs."
            ),
            "author_name": "Ibrahim Solak",
            "author_title": "Head of Growth, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=22),
            "meta_title": "Finance Manager Assessments: Test Strategic Thinking | Evalon",
            "meta_description": "Go beyond spreadsheet tests. Assess finance candidates on FP&A, budgeting, risk management, and strategic capital allocation with structured assessments.",
            "meta_keywords": "finance assessment, finance manager test, FP&A hiring, strategic finance, finance skills test, capital allocation assessment",
            "meta_image": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "assessment-guides",
        },
        # ── 8. Candidate Experience ──
        {
            "title": "Candidate Experience in 2026: Why Your Assessment Process Is Your Employer Brand",
            "slug": "candidate-experience-assessment-employer-brand",
            "hero_image": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Talent Ops",
            "pill_style": "neutral",
            "excerpt": "70% of candidates share negative hiring experiences online. A well-designed assessment process doesn't just evaluate talent—it builds your employer brand with every interaction.",
            "body": (
                "## Your hiring process is a product\n\n"
                "Every touchpoint in your hiring funnel is an experience candidates will remember—and share. Glassdoor reviews, LinkedIn posts, and word-of-mouth referrals are shaped by how candidates *feel* during the process, not just whether they got the job.\n\n"
                "## The assessment experience gap\n\n"
                "Most skills assessments are designed for the employer's convenience, not the candidate's experience. They're timed, stressful, and often irrelevant to the actual role. Candidates complete a four-hour take-home project and never hear back. This destroys your employer brand.\n\n"
                "## How Evalon designs for candidate experience\n\n"
                "### Respect for time\n"
                "Our assessments are designed to take 25–40 minutes, not four hours. Every question maps directly to a skill the role requires. If a question doesn't predict job performance, we remove it.\n\n"
                "### Transparency and context\n"
                "Before starting, candidates see exactly what they'll be assessed on, how long it will take, and how their results will be used. No surprises, no hidden timers, no trick questions.\n\n"
                "### Mobile-first design\n"
                "42% of candidates start assessments on their phone. Evalon's interface is responsive, accessible, and works on any device. Candidates can pause and resume without losing progress.\n\n"
                "### Meaningful feedback\n"
                "Candidates who complete an Evalon assessment can request a summary of their strengths. This turns a one-way evaluation into a two-way value exchange. Candidates appreciate the insight, even if they don't get the job.\n\n"
                "## Five rules for candidate-friendly assessments\n\n"
                "1. **Keep it under 40 minutes.** Anything longer and completion rates drop below 60%.\n"
                "2. **Explain the \"why\" upfront.** Tell candidates what you're evaluating and why it matters for the role.\n"
                "3. **Close the loop within 5 business days.** Silence is the worst feedback.\n"
                "4. **Make it relevant.** Every question should relate to actual job tasks, not abstract brain teasers.\n"
                "5. **Offer value back.** Share results, provide resources, or simply thank candidates for their time with a personal note.\n\n"
                "## The business case for candidate experience\n\n"
                "Companies with strong candidate experience see **28% higher offer acceptance rates** (Talent Board, CandE Research). When you treat candidates well—even the ones you reject—they become advocates. Bad candidate experience costs you referrals, reviews, and eventually, revenue."
            ),
            "author_name": "Anika Patel",
            "author_title": "Director of Product, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=26),
            "meta_title": "Candidate Experience Best Practices for Assessments | Evalon",
            "meta_description": "Your hiring process is your employer brand. Learn how to design candidate-friendly assessments that evaluate talent while building trust and advocacy.",
            "meta_keywords": "candidate experience, employer brand, assessment best practices, candidate-friendly hiring, talent acquisition, hiring process design",
            "meta_image": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "hiring-strategy",
        },
        # ── 9. ROI of Assessments / Pricing justification ──
        {
            "title": "The ROI of Pre-Hire Assessments: What the Data Actually Shows",
            "slug": "roi-pre-hire-assessments-data",
            "hero_image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Insights",
            "pill_style": "success",
            "excerpt": "A bad hire costs 30–150% of their annual salary. Pre-hire assessments cost a fraction of that. Here's how to calculate the return on investment for your organization.",
            "body": (
                "## The cost of a bad hire\n\n"
                "The U.S. Department of Labor estimates a bad hire costs at least 30% of the employee's first-year salary. For senior roles, the Society for Human Resource Management (SHRM) puts the figure at **up to 200%** when you factor in lost productivity, team disruption, and re-recruiting costs.\n\n"
                "For a $100,000 hire, that's $30,000–$200,000 at risk. Pre-hire assessments typically cost $15–$80 per candidate. The math is straightforward.\n\n"
                "## Three ways assessments generate ROI\n\n"
                "### 1. Reduced mis-hires\n"
                "Assessments add a validated data point to your hiring decision. Companies using structured assessments report **24% lower first-year turnover** (Aberdeen Group). If you hire 50 people per year and reduce turnover by even 5 hires, the savings dwarf the assessment cost.\n\n"
                "### 2. Faster time-to-hire\n"
                "Assessments front-load evaluation. Instead of five interview rounds to figure out whether someone can do the job, you start the conversation with data. Evalon customers report a **35% reduction in time-to-hire**, which means open roles get filled faster and revenue loss from vacant positions decreases.\n\n"
                "### 3. Better quality of hire\n"
                "When you measure candidates on job-relevant skills rather than gut feel, you hire people who perform better. Evalon's internal analysis shows that candidates scoring in the top quartile of our assessments are **1.8x more likely** to be rated \"exceeds expectations\" at their six-month review.\n\n"
                "## How to calculate your assessment ROI\n\n"
                "Here's a simple framework:\n\n"
                "**Annual assessment cost** = (candidates assessed × cost per assessment)\n\n"
                "**Annual savings** = (mis-hires avoided × average cost per mis-hire) + (days saved per hire × cost of vacancy per day × hires per year)\n\n"
                "**ROI** = (savings - cost) / cost × 100\n\n"
                "For most mid-market companies hiring 20–100 people per year, the ROI ranges from **500% to 2,000%**.\n\n"
                "## Evalon's pricing in context\n\n"
                "Our Starter plan is free—2 active projects, 20 invites per month, all six assessment banks included. For growing teams, the Pro plan at $59/month supports 10 projects and 250 invites. At scale, Enterprise offers unlimited usage with custom assessments and SSO.\n\n"
                "Every plan includes the same validated assessments. You never pay more for quality—just for volume.\n\n"
                "## Making the business case\n\n"
                "When presenting to leadership, frame assessments as *risk reduction*, not as a line item. A single avoided bad hire pays for years of assessment costs. And unlike most HR investments, the ROI is directly measurable."
            ),
            "author_name": "Ibrahim Solak",
            "author_title": "Head of Growth, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=30),
            "meta_title": "ROI of Pre-Hire Assessments: Data-Backed Analysis | Evalon",
            "meta_description": "Pre-hire assessments deliver 500–2,000% ROI by reducing mis-hires, speeding up hiring, and improving quality of hire. See the full cost-benefit analysis.",
            "meta_keywords": "assessment ROI, pre-hire assessment cost, hiring ROI, cost of bad hire, assessment pricing, hiring analytics",
            "meta_image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "industry-insights",
        },
        # ── 10. API & Integration guide ──
        {
            "title": "Integrating Evalon Assessments into Your ATS: A Technical Guide",
            "slug": "integrating-evalon-assessments-ats-technical-guide",
            "hero_image": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?auto=format&fit=crop&w=1200&q=80",
            "pill_label": "Platform",
            "pill_style": "success",
            "excerpt": "Connect Evalon to your applicant tracking system with our REST API. This guide covers authentication, session management, webhooks, and best practices for production integrations.",
            "body": (
                "## Why integrate via API?\n\n"
                "When assessments live outside your ATS, recruiters context-switch between tabs. Candidates receive emails from multiple systems. Results get lost in spreadsheets. API integration eliminates all of this—assessments become a native step in your existing workflow.\n\n"
                "## Getting started\n\n"
                "### 1. Generate your API key\n"
                "Navigate to your Evalon dashboard → Settings → API Keys. Generate a key and store it securely (never commit it to source control). All API requests require the key in the `Authorization` header:\n\n"
                "```\n"
                "Authorization: Bearer eva_live_xxxxxxxxxxxx\n"
                "```\n\n"
                "### 2. Create an assessment session\n"
                "Send a POST request to start a new assessment:\n\n"
                "```\n"
                "POST /api/v1/sessions/\n"
                "{\n"
                '  "assessment_type": "marketing",\n'
                '  "candidate_email": "jane@example.com",\n'
                '  "candidate_name": "Jane Smith",\n'
                '  "project_id": "proj_abc123"\n'
                "}\n"
                "```\n\n"
                "The response includes a `session_uuid` and a `candidate_url` that you embed in your ATS as a one-click link.\n\n"
                "### 3. Configure webhooks\n"
                "Rather than polling for results, configure a webhook endpoint in your dashboard. Evalon sends a POST request when a session status changes:\n\n"
                "```\n"
                "{\n"
                '  "event": "session.completed",\n'
                '  "session_uuid": "sess_xyz789",\n'
                '  "assessment_type": "marketing",\n'
                '  "score_summary": { "overall": 82, "sections": [...] },\n'
                '  "completed_at": "2026-01-15T14:30:00Z"\n'
                "}\n"
                "```\n\n"
                "### 4. Retrieve the full scorecard\n"
                "After completion, fetch the detailed scorecard:\n\n"
                "```\n"
                "GET /api/v1/sessions/{session_uuid}/scorecard/\n"
                "```\n\n"
                "The scorecard includes section-level scores, individual question performance, and a narrative summary you can display directly in your ATS candidate profile.\n\n"
                "## Best practices for production\n\n"
                "- **Idempotency:** Use the `candidate_email` + `project_id` combination as a natural key. Our API is idempotent—sending the same request twice returns the existing session instead of creating a duplicate.\n"
                "- **Rate limits:** The API allows 100 requests per minute per key. For bulk operations (e.g., inviting an entire cohort), use the batch endpoint.\n"
                "- **Error handling:** All errors return standard HTTP status codes with a `detail` field. Handle 429 (rate limit) with exponential backoff.\n"
                "- **Security:** Rotate API keys quarterly. Use separate keys for staging and production. Never expose keys in client-side code.\n\n"
                "## Popular ATS integrations\n\n"
                "Evalon customers have built integrations with Greenhouse, Lever, Ashby, Workday, and custom ATS platforms. Our API is ATS-agnostic—if your system can make HTTP requests, it can integrate with Evalon.\n\n"
                "Need help? Our platform team offers integration office hours every Thursday. Reach out via the API docs page to book a session."
            ),
            "author_name": "Lena Ortiz",
            "author_title": "Director of Platform, Evalon",
            "status": "published",
            "published_at": now - timedelta(days=35),
            "meta_title": "Evalon API Integration Guide for ATS Systems | Evalon",
            "meta_description": "Connect Evalon assessments to your ATS with our REST API. Step-by-step guide covering authentication, sessions, webhooks, and production best practices.",
            "meta_keywords": "Evalon API, ATS integration, assessment API, hiring API, webhook integration, applicant tracking system, REST API",
            "meta_image": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?auto=format&fit=crop&w=1200&q=80",
            "is_featured": False,
            "category_slug": "product-platform",
        },
    ]

    for payload in posts:
        category_slug = payload.pop("category_slug")
        payload["category"] = categories.get(category_slug)
        BlogPost.objects.update_or_create(
            slug=payload["slug"],
            defaults=payload,
        )

    # Update existing seed posts with categories and SEO metadata
    existing_updates = [
        {
            "slug": "operationalize-behavioral-insights",
            "category_slug": "hiring-strategy",
            "meta_title": "Operationalize Behavioral Insights for Hiring Teams | Evalon",
            "meta_description": "Turn candidate behavioral data into actionable enablement for recruiters and hiring managers. Build handoffs and close the loop with candidates.",
            "meta_keywords": "behavioral insights, hiring enablement, candidate feedback, recruiter tools, hiring packets",
        },
        {
            "slug": "scaling-marketing-assessments",
            "category_slug": "assessment-guides",
            "meta_title": "Scaling Marketing Assessments for Growth Teams | Evalon",
            "meta_description": "Learn how top brands roll out marketing assessments across paid, lifecycle, and analytics squads. Includes a scoring checklist for marketing leaders.",
            "meta_keywords": "marketing assessments, growth teams, marketing hiring, digital marketing test, candidate experience",
        },
        {
            "slug": "api-handbook",
            "category_slug": "product-platform",
            "meta_title": "API Handbook: Integrate Evalon Assessments | Evalon",
            "meta_description": "Step-by-step guide to integrating Evalon with your ATS or workflow tools. Covers authentication, session management, and sample payloads.",
            "meta_keywords": "Evalon API, ATS integration, assessment API, hiring automation, API handbook",
        },
    ]
    for update in existing_updates:
        slug = update.pop("slug")
        cat_slug = update.pop("category_slug")
        update["category"] = categories.get(cat_slug)
        BlogPost.objects.filter(slug=slug).update(**update)


def remove_categories_and_posts(apps, schema_editor):
    BlogPost = apps.get_model("blog", "BlogPost")
    BlogCategory = apps.get_model("blog", "BlogCategory")

    BlogPost.objects.filter(
        slug__in=[
            "complete-guide-structured-hiring",
            "evaluate-marketing-talent-data-driven",
            "hiring-product-managers-beyond-case-interview",
            "assessing-ux-ui-designers-beyond-portfolios",
            "behavioral-assessments-predict-team-success",
            "hiring-hr-professionals-assessment",
            "finance-manager-assessments-strategic-thinking",
            "candidate-experience-assessment-employer-brand",
            "roi-pre-hire-assessments-data",
            "integrating-evalon-assessments-ats-technical-guide",
        ]
    ).delete()

    BlogCategory.objects.filter(
        slug__in=[
            "hiring-strategy",
            "assessment-guides",
            "product-platform",
            "industry-insights",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0004_blogcategory_blogpost_category"),
    ]

    operations = [
        migrations.RunPython(seed_categories_and_posts, remove_categories_and_posts),
    ]
