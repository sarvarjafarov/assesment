from django.core.management.base import BaseCommand

from finance_assessments.models import FinanceQuestion


class Command(BaseCommand):
    help = "Seed the Finance question bank with starter prompts."

    def handle(self, *args, **options):
        created = 0
        for payload in SAMPLE_QUESTIONS:
            obj, was_created = FinanceQuestion.objects.get_or_create(
                question_text=payload["question_text"],
                defaults={k: v for k, v in payload.items() if k != "question_text"},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} questions."))


SAMPLE_QUESTIONS = [
    # ── Financial Planning & Analysis (7 questions) ────────────────────────
    {
        "question_text": "What are the three main financial statements?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "financial_analysis",
        "options": {
            "choices": [
                {"id": "A", "text": "Income statement, balance sheet, and cash flow statement"},
                {"id": "B", "text": "Budget report, variance report, and forecast"},
                {"id": "C", "text": "Trial balance, general ledger, and chart of accounts"},
                {"id": "D", "text": "Tax return, audit report, and annual report"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "The three core financial statements are the income statement (profitability), balance sheet (financial position), and cash flow statement (liquidity). Together they provide a complete picture of financial health.",
    },
    {
        "question_text": "Which financial ratio best measures a company's ability to meet short-term obligations?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "financial_analysis",
        "options": {
            "choices": [
                {"id": "A", "text": "Current ratio (current assets / current liabilities)"},
                {"id": "B", "text": "Debt-to-equity ratio"},
                {"id": "C", "text": "Return on equity"},
                {"id": "D", "text": "Price-to-earnings ratio"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "The current ratio directly measures short-term liquidity by comparing current assets to current liabilities. A ratio above 1 indicates the company can cover near-term obligations.",
    },
    {
        "question_text": "Revenue is up 15% year-over-year but profit margins have shrunk by 8 percentage points. What is your first step as finance manager?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "financial_analysis",
        "options": {
            "choices": [
                {"id": "A", "text": "Perform a detailed cost breakdown and variance analysis to identify which cost categories drove the margin compression"},
                {"id": "B", "text": "Immediately cut discretionary spending across all departments"},
                {"id": "C", "text": "Raise prices to restore margins"},
                {"id": "D", "text": "Report the revenue growth and downplay the margin decline"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Root-cause analysis through cost decomposition prevents knee-jerk reactions. Margin compression could stem from product mix shifts, input cost increases, or scaling inefficiencies—each requiring different remedies.",
    },
    {
        "question_text": "When performing variance analysis, which variance type most directly indicates pricing issues?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "financial_analysis",
        "options": {
            "choices": [
                {"id": "A", "text": "Rate variance (price variance)"},
                {"id": "B", "text": "Volume variance"},
                {"id": "C", "text": "Mix variance"},
                {"id": "D", "text": "Efficiency variance"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Rate (price) variance isolates the impact of actual vs. budgeted prices on financial results, directly flagging pricing issues. Volume variance measures quantity differences, mix variance measures product composition changes.",
    },
    {
        "question_text": "Rank these FP&A deliverables by strategic value to executive decision-making.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "financial_analysis",
        "options": {
            "items": ["Scenario analysis", "Rolling forecast", "Budget vs. actual report", "Monthly close report"]
        },
        "correct_answer": ["Scenario analysis", "Rolling forecast", "Budget vs. actual report", "Monthly close report"],
        "scoring_weight": 1.2,
        "explanation": "Scenario analysis informs strategic decisions under uncertainty; rolling forecasts provide forward-looking agility; budget vs. actual tracks execution; monthly close is backward-looking and operational.",
    },
    {
        "question_text": "The CFO asks for a profitability analysis explaining why margins dropped despite revenue growth. Describe your approach.",
        "question_type": "reasoning",
        "difficulty_level": 4,
        "category": "financial_analysis",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: waterfall analysis of margin drivers, segmentation by product/customer/channel, COGS vs. OpEx breakdown, year-over-year bridge, identification of one-time vs. structural factors, actionable recommendations.",
    },
    {
        "question_text": "When building a 3-statement financial model, which statement serves as the primary driver for the other two?",
        "question_type": "multiple_choice",
        "difficulty_level": 5,
        "category": "financial_analysis",
        "options": {
            "choices": [
                {"id": "A", "text": "Income statement — it drives balance sheet accruals and cash flow adjustments"},
                {"id": "B", "text": "Balance sheet — it determines all other figures"},
                {"id": "C", "text": "Cash flow statement — cash is king"},
                {"id": "D", "text": "All three are built independently"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "In 3-statement modeling, the income statement is built first. Net income flows to retained earnings (balance sheet) and is the starting point for cash flow from operations. Balance sheet changes then feed back into the cash flow statement.",
    },

    # ── Budgeting & Cost Management (6 questions) ─────────────────────────
    {
        "question_text": "What is zero-based budgeting?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "budgeting",
        "options": {
            "choices": [
                {"id": "A", "text": "Every expense must be justified from zero each budget period"},
                {"id": "B", "text": "Starting the budget at zero and adding a fixed percentage"},
                {"id": "C", "text": "Eliminating all expenses and rebuilding the company"},
                {"id": "D", "text": "Setting all department budgets to the same amount"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Zero-based budgeting requires each cost to be justified from scratch every period, rather than simply adjusting the previous year's budget. This eliminates legacy spending and forces critical evaluation.",
    },
    {
        "question_text": "Which budgeting approach is best suited for a rapidly growing startup with uncertain revenue?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "budgeting",
        "options": {
            "choices": [
                {"id": "A", "text": "Rolling forecast updated monthly or quarterly"},
                {"id": "B", "text": "Fixed annual budget set at the beginning of the year"},
                {"id": "C", "text": "Zero-based budgeting"},
                {"id": "D", "text": "Incremental budgeting based on prior year"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Rolling forecasts provide the flexibility startups need by continuously updating projections as new data becomes available, rather than locking into annual assumptions that quickly become outdated.",
    },
    {
        "question_text": "Department heads collectively request 25% more budget than the available allocation. How do you handle this as finance manager?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "budgeting",
        "options": {
            "choices": [
                {"id": "A", "text": "Facilitate a prioritization exercise with ROI analysis, align requests to strategic goals, and negotiate tradeoffs transparently"},
                {"id": "B", "text": "Cut everyone's request by 25% equally"},
                {"id": "C", "text": "Approve all requests and find the extra budget later"},
                {"id": "D", "text": "Escalate to the CEO and let them decide"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "ROI-based prioritization ensures capital flows to the highest-value initiatives. Equal cuts penalize efficient departments and reward those who over-request. Transparent tradeoff discussions build cross-functional trust.",
    },
    {
        "question_text": "What is the primary advantage of activity-based costing over traditional cost allocation?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "budgeting",
        "options": {
            "choices": [
                {"id": "A", "text": "Allocates overhead costs more accurately based on actual resource consumption"},
                {"id": "B", "text": "Simpler to implement and maintain"},
                {"id": "C", "text": "Requires less data collection"},
                {"id": "D", "text": "Eliminates the need for cost centers"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Activity-based costing traces overhead to specific activities and their cost drivers, providing more accurate product and service costing than volume-based allocation methods.",
    },
    {
        "question_text": "Rank these cost reduction strategies by long-term sustainability.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "budgeting",
        "options": {
            "items": ["Process optimization and automation", "Vendor renegotiation", "Technology investment", "Headcount reduction"]
        },
        "correct_answer": ["Process optimization and automation", "Technology investment", "Vendor renegotiation", "Headcount reduction"],
        "scoring_weight": 1.2,
        "explanation": "Process optimization creates permanent efficiency gains; technology investment scales savings; vendor renegotiation yields near-term savings but requires renewal; headcount cuts are quick but can damage capacity and morale.",
    },
    {
        "question_text": "Design a budgeting process for a 200-person company transitioning from annual budgets to rolling forecasts. Describe the key steps and change management approach.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "budgeting",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: stakeholder buy-in strategy, driver-based model design, technology/tool selection, training plan, phased rollout, cadence definition (monthly vs quarterly updates), KPI alignment, pilot department selection.",
    },

    # ── Risk Management & Compliance (5 questions) ────────────────────────
    {
        "question_text": "What is the primary purpose of SOX (Sarbanes-Oxley) compliance?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "risk_compliance",
        "options": {
            "choices": [
                {"id": "A", "text": "Ensure accuracy and reliability of corporate financial reporting"},
                {"id": "B", "text": "Reduce corporate tax obligations"},
                {"id": "C", "text": "Standardize employee benefits across companies"},
                {"id": "D", "text": "Regulate international trade agreements"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "SOX was enacted after Enron and WorldCom scandals to protect investors by improving the accuracy and reliability of corporate disclosures, with specific requirements for internal controls over financial reporting.",
    },
    {
        "question_text": "Which internal control is most effective at preventing fraudulent disbursements?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "risk_compliance",
        "options": {
            "choices": [
                {"id": "A", "text": "Segregation of duties between authorization, custody, and recording"},
                {"id": "B", "text": "Requiring receipts for all purchases"},
                {"id": "C", "text": "Annual external audit"},
                {"id": "D", "text": "Employee background checks"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Segregation of duties ensures no single person controls an entire transaction from initiation through recording. This is the most fundamental preventive control in the COSO internal control framework.",
    },
    {
        "question_text": "An internal audit reveals a material weakness in revenue recognition processes. What is your remediation approach?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "risk_compliance",
        "options": {
            "choices": [
                {"id": "A", "text": "Quantify the impact, design enhanced controls, retrain staff, implement monitoring, and disclose as required"},
                {"id": "B", "text": "Minimize the finding and address it next quarter"},
                {"id": "C", "text": "Replace the entire accounting team"},
                {"id": "D", "text": "Hire an external firm to handle all revenue recognition"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Material weaknesses require prompt remediation with quantified impact assessment, control redesign, training, ongoing monitoring, and appropriate disclosure to auditors and regulators.",
    },
    {
        "question_text": "When assessing enterprise financial risk, which framework provides the most comprehensive approach?",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "risk_compliance",
        "options": {
            "choices": [
                {"id": "A", "text": "COSO Enterprise Risk Management (ERM) framework"},
                {"id": "B", "text": "Simple risk register spreadsheet"},
                {"id": "C", "text": "Insurance coverage review only"},
                {"id": "D", "text": "Annual financial statement analysis"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "COSO ERM integrates risk management with strategy and performance, covering governance, strategy, performance, review, and communication across all risk categories.",
    },
    {
        "question_text": "Describe how you would implement an enterprise risk management framework for a mid-size company preparing for an IPO.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "risk_compliance",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: risk assessment workshop design, risk appetite statement, risk taxonomy, control environment evaluation, SOX 302/404 readiness, board risk committee formation, risk reporting cadence, IT general controls, third-party risk assessment.",
    },

    # ── Strategic Finance (6 questions) ───────────────────────────────────
    {
        "question_text": "What does WACC stand for and what does it measure?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "strategic_finance",
        "options": {
            "choices": [
                {"id": "A", "text": "Weighted Average Cost of Capital — the blended cost of all financing sources"},
                {"id": "B", "text": "Working Assets and Capital Costs — total operating expenses"},
                {"id": "C", "text": "Weighted Allocation of Corporate Cash — how cash is distributed"},
                {"id": "D", "text": "Wholesale Average Credit Cost — borrowing rates"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "WACC represents the weighted average return required by all capital providers (debt and equity). It serves as the discount rate for evaluating investments and is the minimum hurdle rate for value creation.",
    },
    {
        "question_text": "When evaluating a potential acquisition, which valuation method provides the most intrinsic estimate of value?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "strategic_finance",
        "options": {
            "choices": [
                {"id": "A", "text": "Discounted cash flow (DCF) analysis"},
                {"id": "B", "text": "Comparable company multiples only"},
                {"id": "C", "text": "Book value of assets"},
                {"id": "D", "text": "Revenue multiple"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "DCF analysis values a business based on its projected future cash flows discounted to present value, capturing the intrinsic value of the business rather than relying on market comparisons.",
    },
    {
        "question_text": "The CEO wants to pursue an acquisition at 12x EBITDA when the industry average is 8x. How do you advise?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "strategic_finance",
        "options": {
            "choices": [
                {"id": "A", "text": "Build a detailed synergy model to quantify whether the premium is justified, present risk-adjusted scenarios to the board"},
                {"id": "B", "text": "Support the CEO's decision without analysis to maintain the relationship"},
                {"id": "C", "text": "Refuse to participate in the deal"},
                {"id": "D", "text": "Approve the deal if the company can afford the purchase price"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "A 50% premium over industry average requires rigorous justification through synergy quantification, integration cost modeling, and scenario analysis. Finance's role is to provide objective data for decision-making.",
    },
    {
        "question_text": "Which capital structure decision has the greatest impact on a company's weighted average cost of capital?",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "strategic_finance",
        "options": {
            "choices": [
                {"id": "A", "text": "Optimizing the debt-to-equity ratio to balance tax shields against financial distress costs"},
                {"id": "B", "text": "Choosing between different bank lenders"},
                {"id": "C", "text": "Timing of dividend payments"},
                {"id": "D", "text": "Selection of accounting methods"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "The debt-to-equity mix directly determines WACC through the tradeoff between the tax benefit of debt (interest deductibility) and the increasing cost of financial distress at higher leverage levels.",
    },
    {
        "question_text": "Rank these investment evaluation methods by reliability for capital allocation decisions.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "strategic_finance",
        "options": {
            "items": ["Net Present Value (NPV)", "Internal Rate of Return (IRR)", "Return on Investment (ROI)", "Payback period"]
        },
        "correct_answer": ["Net Present Value (NPV)", "Internal Rate of Return (IRR)", "Return on Investment (ROI)", "Payback period"],
        "scoring_weight": 1.2,
        "explanation": "NPV directly measures value creation in dollar terms; IRR gives a return percentage but can mislead with non-conventional cash flows; ROI is simple but ignores time value; payback ignores cash flows beyond the payback period.",
    },
    {
        "question_text": "Describe your approach to building a business case for a $50M capital investment in new manufacturing capacity, including the financial analysis framework and key assumptions.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "strategic_finance",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: NPV/IRR analysis, revenue and cost projections, capacity utilization assumptions, sensitivity analysis on key variables, scenario modeling (base/bull/bear), payback timeline, strategic alignment, risk factors, financing options comparison.",
    },

    # ── Accounting & Operations (5 questions) ─────────────────────────────
    {
        "question_text": "Under GAAP, when should revenue be recognized?",
        "question_type": "multiple_choice",
        "difficulty_level": 1,
        "category": "accounting_ops",
        "options": {
            "choices": [
                {"id": "A", "text": "When performance obligations are satisfied (ASC 606)"},
                {"id": "B", "text": "When cash is received"},
                {"id": "C", "text": "When the contract is signed"},
                {"id": "D", "text": "At the end of the fiscal year"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "ASC 606 (Revenue from Contracts with Customers) requires revenue recognition when performance obligations are satisfied — when control of goods or services transfers to the customer.",
    },
    {
        "question_text": "What is the primary purpose of an account reconciliation?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "accounting_ops",
        "options": {
            "choices": [
                {"id": "A", "text": "Verify that account balances are accurate by comparing records between two or more systems"},
                {"id": "B", "text": "Calculate tax obligations"},
                {"id": "C", "text": "Generate financial reports for investors"},
                {"id": "D", "text": "Approve vendor payments"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Account reconciliations compare balances between the general ledger and subsidiary records (bank statements, sub-ledgers, third-party systems) to ensure accuracy and identify discrepancies.",
    },
    {
        "question_text": "During month-end close, you discover a $500K unreconciled difference in the accounts receivable sub-ledger. What is your first step?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "accounting_ops",
        "options": {
            "choices": [
                {"id": "A", "text": "Investigate the source and timing of the discrepancy before closing the books"},
                {"id": "B", "text": "Close the books and investigate next month"},
                {"id": "C", "text": "Write off the difference as bad debt"},
                {"id": "D", "text": "Adjust the sub-ledger to match the GL without investigation"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "A $500K discrepancy is material and must be investigated before closing. It could indicate timing differences, posting errors, or control failures. Closing without resolution masks potential issues.",
    },
    {
        "question_text": "Your month-end close process currently takes 15 business days. Leadership wants it completed in 5 days. What is your plan?",
        "question_type": "scenario",
        "difficulty_level": 4,
        "category": "accounting_ops",
        "options": {
            "choices": [
                {"id": "A", "text": "Map the current process, identify bottlenecks, automate reconciliations, implement pre-close checklists, and run a phased improvement plan"},
                {"id": "B", "text": "Simply skip non-critical reconciliations to save time"},
                {"id": "C", "text": "Hire more staff to work in parallel"},
                {"id": "D", "text": "Tell leadership it's impossible"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "Process mapping reveals bottlenecks (manual reconciliations, data dependencies, approval delays). Automation, pre-close activities, and parallel workstreams can dramatically reduce close timelines without sacrificing accuracy.",
    },
    {
        "question_text": "Describe how you would manage a company's transition from GAAP to IFRS reporting, including key differences and implementation challenges.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "accounting_ops",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: gap analysis of key differences (lease accounting, revenue recognition, inventory), dual reporting period, system configuration, staff training, audit firm coordination, investor communication, timeline with milestones.",
    },

    # ── Treasury & Cash Management (6 questions) ─────────────────────────
    {
        "question_text": "What is the primary objective of working capital management?",
        "question_type": "multiple_choice",
        "difficulty_level": 2,
        "category": "treasury",
        "options": {
            "choices": [
                {"id": "A", "text": "Optimize liquidity to meet obligations while minimizing the cost of holding idle cash"},
                {"id": "B", "text": "Maximize cash on hand at all times"},
                {"id": "C", "text": "Eliminate all accounts payable"},
                {"id": "D", "text": "Invest all cash in long-term securities"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "Working capital management balances the need for sufficient liquidity (to pay bills and operate) against the opportunity cost of idle cash. The goal is optimization, not maximization.",
    },
    {
        "question_text": "Which cash flow forecasting method is most appropriate for a 13-week cash forecast?",
        "question_type": "multiple_choice",
        "difficulty_level": 3,
        "category": "treasury",
        "options": {
            "choices": [
                {"id": "A", "text": "Direct method using detailed receipts and disbursements"},
                {"id": "B", "text": "Indirect method starting from net income"},
                {"id": "C", "text": "Percentage-of-revenue method"},
                {"id": "D", "text": "Historical average method"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.0,
        "explanation": "The direct method tracks actual expected cash inflows and outflows, providing the granularity needed for short-term (13-week) forecasting. The indirect method is better suited for longer-term projections.",
    },
    {
        "question_text": "Your company's cash runway is 4 months and revenue is 20% below forecast. What is your immediate action plan?",
        "question_type": "scenario",
        "difficulty_level": 3,
        "category": "treasury",
        "options": {
            "choices": [
                {"id": "A", "text": "Build a weekly cash forecast, identify non-essential spend to defer, negotiate extended payment terms, and prepare a bridge financing plan"},
                {"id": "B", "text": "Continue normal operations and hope revenue recovers"},
                {"id": "C", "text": "Immediately lay off 50% of staff"},
                {"id": "D", "text": "Draw down the entire credit facility as a precaution"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "A 4-month runway with declining revenue demands immediate cash preservation: tighter forecasting cadence, expense management, vendor negotiation, and proactive financing—not panic or inaction.",
    },
    {
        "question_text": "When managing foreign exchange risk, which hedging instrument provides the most flexibility?",
        "question_type": "multiple_choice",
        "difficulty_level": 4,
        "category": "treasury",
        "options": {
            "choices": [
                {"id": "A", "text": "FX options — they provide the right but not the obligation to exchange at a set rate"},
                {"id": "B", "text": "Forward contracts"},
                {"id": "C", "text": "Natural hedging only"},
                {"id": "D", "text": "Currency swaps"},
            ]
        },
        "correct_answer": "A",
        "scoring_weight": 1.2,
        "explanation": "FX options provide downside protection while preserving upside potential. Unlike forwards (which lock in a rate), options allow the holder to benefit from favorable rate movements while limiting losses.",
    },
    {
        "question_text": "Rank these cash management priorities for a company approaching a debt covenant threshold.",
        "question_type": "ranking",
        "difficulty_level": 4,
        "category": "treasury",
        "options": {
            "items": ["Debt covenant compliance", "Operating cash reserves", "Vendor payment terms optimization", "Investment returns on excess cash"]
        },
        "correct_answer": ["Debt covenant compliance", "Operating cash reserves", "Vendor payment terms optimization", "Investment returns on excess cash"],
        "scoring_weight": 1.2,
        "explanation": "Covenant breach triggers default provisions and potential acceleration of debt; operating reserves ensure business continuity; vendor terms extend cash runway; investment returns are lowest priority in a liquidity crisis.",
    },
    {
        "question_text": "Design a cash management strategy for a company expanding operations to 5 international markets, covering FX risk, banking structure, and intercompany funding.",
        "question_type": "reasoning",
        "difficulty_level": 5,
        "category": "treasury",
        "options": {},
        "correct_answer": None,
        "scoring_weight": 1.4,
        "explanation": "Look for: multi-currency cash pooling structure, FX hedging policy, banking partner selection criteria, intercompany loan framework (transfer pricing), cash repatriation strategy, local regulatory considerations, payment infrastructure.",
    },

    # ── Behavioral (5 questions) ──────────────────────────────────────────
    {
        "question_text": "When presenting financial results to non-finance stakeholders, you tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 2,
        "category": "behavioral",
        "options": {
            "statements": [
                "Simplify with visual dashboards and focus on business implications",
                "Share the raw data and let them draw conclusions",
                "Present detailed spreadsheets with full methodology",
                "Only share the summary numbers without context",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "When you discover a financial reporting error after the books are closed, you would least likely...",
        "question_type": "behavioral_least",
        "difficulty_level": 2,
        "category": "behavioral",
        "options": {
            "statements": [
                "Ignore it if the amount seems immaterial",
                "Immediately notify your manager and assess the impact",
                "Correct it in the next period with a prior-period adjustment",
                "Document it and wait for the auditors to find it",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "Facing pressure from a business unit leader to approve aggressive revenue assumptions in the forecast, you tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 3,
        "category": "behavioral",
        "options": {
            "statements": [
                "Push back with data, present historical accuracy of similar assumptions, and propose a risk-adjusted range",
                "Accept their assumptions to avoid conflict",
                "Reject the forecast entirely and substitute your own numbers",
                "Escalate to the CFO without discussing with the business unit leader first",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "A business unit leader asks you to approve an unbudgeted $200K expense that they say is critical. You would least likely...",
        "question_type": "behavioral_least",
        "difficulty_level": 3,
        "category": "behavioral",
        "options": {
            "statements": [
                "Approve immediately to maintain the relationship",
                "Request a business case with ROI analysis before deciding",
                "Deny it outright without discussion",
                "Suggest they find offsetting savings within their existing budget",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
    {
        "question_text": "Your team disagrees on the financial model assumptions for a critical board presentation. You tend to...",
        "question_type": "behavioral_most",
        "difficulty_level": 4,
        "category": "behavioral",
        "options": {
            "statements": [
                "Facilitate a data-driven discussion, stress-test each assumption, and build consensus around defensible numbers",
                "Use the most conservative assumptions to be safe",
                "Let the most senior analyst make the final call",
                "Present multiple versions and let the board decide",
            ]
        },
        "correct_answer": None,
        "scoring_weight": 0.8,
    },
]
