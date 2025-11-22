from django.db import migrations


def sync_plan_defaults(apps, schema_editor):
    ClientAccount = apps.get_model('clients', 'ClientAccount')
    plan_map = {
        'starter': {'project_quota': 2, 'invite_quota': 20},
        'pro': {'project_quota': 10, 'invite_quota': 250},
        'growth': {'project_quota': 25, 'invite_quota': 750},
        'enterprise': {'project_quota': 0, 'invite_quota': 0},
    }
    for account in ClientAccount.objects.all():
        plan = plan_map.get(account.plan_slug or 'starter', plan_map['starter'])
        account.plan_slug = account.plan_slug or 'starter'
        account.project_quota = plan['project_quota']
        account.invite_quota = plan['invite_quota']
        account.save(update_fields=['plan_slug', 'project_quota', 'invite_quota'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_alter_clientaccount_plan_slug'),
    ]

    operations = [
        migrations.RunPython(sync_plan_defaults, noop),
    ]
