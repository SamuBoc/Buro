from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0004_add_administrador_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaseReassignmentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reassignment_logs', to='cases.case', verbose_name='Caso')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='case_reassignment_logs', to=settings.AUTH_USER_MODEL, verbose_name='Reasignado por')),
                ('new_student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Estudiante nuevo')),
                ('old_student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Estudiante anterior')),
            ],
            options={
                'verbose_name': 'Bitacora de reasignacion',
                'verbose_name_plural': 'Bitacora de reasignaciones',
                'ordering': ['-created_at'],
            },
        ),
    ]