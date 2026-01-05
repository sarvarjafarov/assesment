/**
 * Evalon Onboarding Tour Steps
 * Defines the sequence and content of the guided tour
 */

const onboardingSteps = [
    {
        title: "Welcome to Evalon!",
        message: "Let's take a quick tour to help you get started. We'll show you how to invite candidates, track progress, and make hiring decisions.",
        target: ".dashboard-page-header",
        scrollTo: true
    },
    {
        title: "Your Performance Dashboard",
        message: "Track your hiring metrics at a glance: completion rates, average duration, and candidate scores.",
        target: ".key-metrics",
        scrollTo: true
    },
    {
        title: "Quick Actions",
        message: "Access key features quickly from these shortcuts: Assessments, Projects, Analytics, and Data Export.",
        target: ".quick-links-grid",
        scrollTo: true
    },
    {
        title: "Browse Assessments",
        message: "Click here to see all available assessments. Each assessment is designed for specific roles and skills.",
        target: ".nav-item[href*='assessments']",
        scrollTo: false,
        onShow: (tour) => {
            // Optional: Add visual pulse effect
            document.querySelector(".nav-item[href*='assessments']")?.classList.add('pulse-highlight');
        }
    },
    {
        title: "Organize with Projects",
        message: "Group candidates by role or position. Projects help you track hiring pipelines and collaborate with your team.",
        target: ".nav-item[href*='projects']",
        scrollTo: false
    },
    {
        title: "Review Results",
        message: "After candidates complete assessments, view detailed reports here. You'll see scores, insights, and recommendations.",
        target: ".recent-activity-section",
        scrollTo: true
    },
    {
        title: "Track Analytics",
        message: "Monitor trends over time: completion rates, score distributions, and performance benchmarks.",
        target: ".nav-item[href*='analytics']",
        scrollTo: false
    },
    {
        title: "You're All Set!",
        message: "That's it! Start by inviting your first candidate. Need help? Check Settings for tour replay and support links.",
        target: ".primary-action-card",
        scrollTo: true
    }
];

// Role-specific step filters
const getRoleSteps = (userRole) => {
    if (userRole === 'viewer') {
        // Viewers can't create invites, focus on viewing
        return onboardingSteps.filter(step =>
            !step.title.includes('Invite') && !step.title.includes('Organize')
        );
    }
    return onboardingSteps; // Full tour for managers/recruiters
};
