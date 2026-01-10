# Welcome Email Content - Auto-Sends on Approval

## 📧 Email Details

**Trigger:** Automatically sent when admin changes client status to "Approved" in Django admin

**Subject:** `Welcome to Evalon, {Full Name}! 🎉`

**From:** `Evalon <info@evalon.tech>`

---

## 📄 Email Structure

### 1. **Header Section**
- Celebration banner with gradient background (navy blue)
- "🎉 Welcome to Evalon!" headline
- "Your account has been approved" subtitle

### 2. **Personal Greeting**
```
Hi {Full Name},

Great news! Your Evalon account for {Company Name} has been approved
and is ready to use.

You now have access to our hiring assessment platform and can start
evaluating candidates right away.
```

### 3. **Big Call-to-Action Button**
```
[Go to Dashboard] → {SITE_URL}/clients/dashboard/
```

### 4. **Account Details Card**
Shows their plan information:
- **Plan:** Starter / Pro / Enterprise
- **Monthly Projects:** 2 (or Unlimited)
- **Monthly Invites:** 20 (or Unlimited)

### 5. **Approved Assessments**
Lists the assessments admin approved (pulled from `allowed_assessments` field):
- ✓ Marketing Assessment
- ✓ Product Management Assessment
- ✓ Behavioral Assessment

**Link:** [Browse Assessments →] → `{SITE_URL}/clients/assessments/`

### 6. **Getting Started Guide (3 Steps)**

#### **Step 1: Create Your First Project**
- Description: Set up a hiring project for each role
- **Link:** [Create Project →] → `{SITE_URL}/clients/dashboard/projects/`

#### **Step 2: Send Candidate Invites**
- Description: Invite candidates with personalized links
- **Link:** [View Assessments →] → `{SITE_URL}/clients/assessments/`

#### **Step 3: Review Auto-Scored Results**
- Description: See detailed reports with scores and recommendations
- No link (informational)

### 7. **Resources Section**
Help box with useful links:
- How Evalon Works
- Best Practices for Assessment Invites
- Contact Support

### 8. **Footer**
- Support contact: support@evalon.app
- Welcome message from team
- Branding and copyright

---

## 🔗 All Internal Links

| Link Text | URL | Purpose |
|-----------|-----|---------|
| Go to Dashboard | `/clients/dashboard/` | Main dashboard access |
| Browse Assessments | `/clients/assessments/` | View assessment catalog |
| Create Project | `/clients/dashboard/projects/` | Start first hiring project |
| View Assessments | `/clients/assessments/` | Access invite management |
| Contact Support | `mailto:support@evalon.app` | Get help |
| evalon.tech | `{SITE_URL}` | Website link |

---

## 📊 Dynamic Content

The email includes personalized data:
- `{{ full_name }}` - User's full name
- `{{ company_name }}` - Company name
- `{{ plan_name }}` - Current plan (Starter/Pro/Enterprise)
- `{{ project_quota }}` - Number of allowed projects
- `{{ invite_quota }}` - Number of allowed invites
- `{{ approved_assessments }}` - List of assessments admin approved

---

## ✅ Implementation Status

**Admin Panel:**
- ✅ Welcome email auto-sends when status changed to "Approved"
- ✅ Admin sees success message: "Welcome email sent to {email}"
- ✅ If email fails, admin sees warning
- ✅ Email uses approved assessments (not requested)

**Email Configuration:**
- ✅ SMTP: Brevo (smtp-relay.brevo.com)
- ✅ From: info@evalon.tech
- ✅ HTML + Plain text versions
- ✅ Mobile responsive design
- ✅ Proper link generation with SITE_URL

---

## 🧪 Testing

To test the welcome email:

```bash
# 1. Approve an account via command
.venv/bin/python manage.py approve_account email@example.com

# 2. Or approve in Django admin:
# - Go to /admin/clients/clientaccount/
# - Click on account
# - Set "Allowed assessments" field
# - Change "Status" to "Approved"
# - Save
# - Welcome email sends automatically!
```

---

## 🎨 Email Design Features

- ✅ Professional gradient header
- ✅ Clear visual hierarchy
- ✅ Numbered steps with circular badges
- ✅ Action buttons with orange brand color
- ✅ Clean, readable typography
- ✅ Mobile-responsive layout
- ✅ Inline CSS for email client compatibility
