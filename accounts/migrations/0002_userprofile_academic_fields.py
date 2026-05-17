from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='availability',
            field=models.BooleanField(default=True, verbose_name='Disponible'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='preferred_room',
            field=models.CharField(
                blank=True,
                choices=[
                    ('civil', 'Civil'),
                    ('laboral', 'Laboral'),
                    ('penal', 'Penal'),
                    ('publico', 'Publico'),
                    ('familia', 'Familia'),
                ],
                max_length=20,
                null=True,
                verbose_name='Sala preferente',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='student_code',
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                unique=True,
                verbose_name='Codigo estudiantil',
            ),
        ),
    ]
