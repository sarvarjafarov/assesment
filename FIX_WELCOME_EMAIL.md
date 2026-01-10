# Fix: Welcome Email Not Sent

## Issue
User approved an account in Heroku admin but the welcome email wasn't sent.

## Possible Causes
1. **Heroku code not updated** - The admin save_model fix wasn't deployed yet
2. **Email sending error** - Brevo SMTP error on Heroku
3. **Missing allowed_assessments** - No assessments were set before approval
4. **Heroku environment variables** - SITE_URL or email config missing

---

## Solution 1: Check Heroku Logs

```bash
# View recent logs to see if there was an error
heroku logs --tail --app assesement-7249edf30d7

# Or check logs from last hour
heroku logs --num 500 --app assesement-7249edf30d7 | grep -i "email\|welcome\|error"
```

Look for errors like:
- "Failed to send welcome email"
- SMTP connection errors
- "Reverse for 'projects' not found" (should be fixed now)

---

## Solution 2: Deploy Latest Code to Heroku

The fixes we made need to be deployed:

```bash
# 1. Commit all changes
git add -A
git commit -m "Fix welcome email and admin panel issues"

# 2. Push to Heroku
git push heroku main

# 3. Restart Heroku
heroku restart --app assesement-7249edf30d7
```

---

## Solution 3: Manually Send Welcome Email

### Option A: Via Heroku CLI

```bash
# Get the user's email (replace with actual email)
heroku run python manage.py send_welcome_email user@example.com --app assesement-7249edf30d7
```

### Option B: Via Heroku Shell

```bash
# Open Heroku shell
heroku run python manage.py shell --app assesement-7249edf30d7

# Then run:
from clients.models import ClientAccount
from clients.services import send_welcome_email

# Find the user (replace with actual email)
account = ClientAccount.objects.get(email='user@example.com')

# Send welcome email
result = send_welcome_email(account)
print(f"Email sent: {result}")
```

---

## Solution 4: Check Heroku Environment Variables

Make sure these are set on Heroku:

```bash
# Check if variables exist
heroku config --app assesement-7249edf30d7 | grep -E "SITE_URL|EMAIL|ADMIN"

# Set if missing:
heroku config:set SITE_URL=https://assesement-7249edf30d7.herokuapp.com --app assesement-7249edf30d7
heroku config:set ADMIN_NOTIFICATION_EMAILS=sarvar@pethoven.com,info@evalon.tech --app assesement-7249edf30d7
```

---

## Solution 5: Find and Email the New User

### Step 1: Find Recent Signups on Heroku

```bash
heroku run python manage.py shell --app assesement-7249edf30d7
```

Then in the shell:
```python
from clients.models import ClientAccount
from django.utils import timezone
from datetime import timedelta

# Find accounts created in last 24 hours
recent = timezone.now() - timedelta(days=1)
accounts = ClientAccount.objects.filter(created_at__gte=recent).order_by('-created_at')

for account in accounts:
    print(f"""
Email: {account.email}
Company: {account.company_name}
Name: {account.full_name}
Status: {account.status}
Verified: {account.is_email_verified}
Allowed: {account.allowed_assessments}
Created: {account.created_at}
---""")
```

### Step 2: Send Welcome Email to That User

```python
from clients.services import send_welcome_email

# Replace with actual email from above
account = ClientAccount.objects.get(email='actual@email.com')

# Make sure they have allowed_assessments set
if not account.allowed_assessments:
    account.allowed_assessments = ['marketing', 'product', 'behavioral']  # Or whatever you approved
    account.save()

# Send welcome email
result = send_welcome_email(account)
print(f"Welcome email sent: {result}")
```

---

## Prevention: Deploy Code First

To prevent this in the future:

```bash
# Always deploy latest code to Heroku after making changes locally
git push heroku main
```

---

## Quick Fix Command (All-in-One)

```bash
# Deploy latest code
git add -A && git commit -m "Fix welcome email" && git push heroku main

# Find and email the new user
heroku run python manage.py shell --app assesement-7249edf30d7 -c "
from clients.models import ClientAccount
from clients.services import send_welcome_email
from django.utils import timezone
from datetime import timedelta

# Find recent approved accounts
recent = timezone.now() - timedelta(days=1)
accounts = ClientAccount.objects.filter(
    status='approved',
    created_at__gte=recent
).exclude(email='sarvar@pethoven.com')

print(f'Found {accounts.count()} recently approved accounts')
for account in accounts:
    print(f'Sending welcome email to {account.email}...')
    result = send_welcome_email(account)
    print(f'Result: {result}')
"
```

---

## Testing the Fix

After deploying, test by:

1. Creating a new test account
2. Verifying email
3. Approving in Heroku admin
4. Checking that welcome email is received
5. Looking at Heroku logs: `heroku logs --tail`

---

## Success Indicators

When working correctly, you should see in Heroku logs:
```
Welcome email sent to user@example.com
```

And the admin panel should show:
```
✓ Welcome email sent to user@example.com
```
