from django.db import migrations


def create_default_groups(apps, schema_editor):
    group_model = apps.get_model('auth', 'Group')

    for group_name in ['secretaria', 'estudiante', 'profesor']:
        group_model.objects.get_or_create(name=group_name)


def remove_default_groups(apps, schema_editor):
    group_model = apps.get_model('auth', 'Group')
    group_model.objects.filter(name__in=['secretaria', 'estudiante', 'profesor']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0002_case_assigned_student'),
    ]

    operations = [
        migrations.RunPython(create_default_groups, remove_default_groups),
    ]
