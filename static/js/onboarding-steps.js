/**
 * Evalon Onboarding Tour Steps
 * Defines the sequence and content of the guided tour
 */

const onboardingSteps = [
    {
        title: "Welcome to Evalon!",
        message: "Let's take a quick tour of your hiring dashboard. We'll show you how to create positions, invite candidates, and make data-driven hiring decisions.",
        target: ".db-header",
        scrollTo: true
    },
    {
        title: "Your Vacancy Page",
        message: "This is your public careers page. Share this link with candidates — anyone who applies will automatically appear in your Candidates list.",
        target: ".db-vacancy-bar",
        scrollTo: true
    },
    {
        title: "Hiring Metrics",
        message: "Track completion rates, average duration, and candidate scores at a glance. These update automatically as candidates complete assessments.",
        target: ".db-metrics",
        scrollTo: true
    },
    {
        title: "Jobs & Positions",
        message: "Create and manage your open positions here. Each position can have its own assessment pipeline and AI screening settings.",
        target: ".nav-item[href*='projects']",
        scrollTo: false
    },
    {
        title: "Your Candidates",
        message: "All applications land here. You can filter by position, status, or AI screening score. Click any candidate to see full details and take action.",
        target: ".nav-item[href*='applications']",
        scrollTo: false
    },
    {
        title: "You're All Set!",
        message: "Start by creating your first position. You can always restart this tour from Settings.",
        target: ".db-header-cta",
        scrollTo: true
    }
];

// AI Screening step — inserted for Pro/Enterprise plans
const aiScreeningStep = {
    title: "AI Screening",
    message: "Your plan includes AI-powered candidate screening. When creating a position, toggle 'Enable AI Screening' to automatically score and filter applicants.",
    target: ".nav-item[href*='projects']",
    scrollTo: false
};

// Build steps based on user role and plan
const buildTourSteps = (userRole, canUseAI) => {
    let steps = [...onboardingSteps];

    // Insert AI step after "Jobs & Positions" (index 3) for Pro/Enterprise
    if (canUseAI) {
        steps.splice(4, 0, aiScreeningStep);
    }

    // Viewers can't create positions — remove Jobs step
    if (userRole === 'viewer') {
        steps = steps.filter(step =>
            step.title !== 'Jobs & Positions' && step.title !== 'AI Screening'
        );
    }

    return steps;
};
