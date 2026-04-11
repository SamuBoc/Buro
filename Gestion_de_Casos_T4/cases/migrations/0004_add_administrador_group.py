from django.db import migrations


def add_administrador_group(apps, schema_editor):
    group_model = apps.get_model('auth', 'Group')
    group_model.objects.get_or_create(name='administrador')


def remove_administrador_group(apps, schema_editor):
    group_model = apps.get_model('auth', 'Group')
    group_model.objects.filter(name='administrador').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_create_default_groups'),
    ]

    operations = [
        migrations.RunPython(add_administrador_group, remove_administrador_group),
    ]
