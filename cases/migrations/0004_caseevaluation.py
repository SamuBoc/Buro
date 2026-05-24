from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_merge_20260519_2315'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CaseEvaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Puntaje')),
                ('feedback', models.TextField(verbose_name='Retroalimentacion')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='cases.case', verbose_name='Caso')),
                ('professor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='given_evaluations', to=settings.AUTH_USER_MODEL, verbose_name='Profesor')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='case_evaluations', to=settings.AUTH_USER_MODEL, verbose_name='Estudiante')),
            ],
            options={
                'verbose_name': 'Evaluacion de caso',
                'verbose_name_plural': 'Evaluaciones de caso',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='caseevaluation',
            index=models.Index(fields=['student', '-created_at'], name='cases_casee_student_6a0f58_idx'),
        ),
        migrations.AddIndex(
            model_name='caseevaluation',
            index=models.Index(fields=['case', '-created_at'], name='cases_casee_case_f0b41e_idx'),
        ),
    ]
