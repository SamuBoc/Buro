from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beneficiary', '0004_alter_beneficiaryauditlog_action'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataDeletionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_date', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')),
                ('status', models.CharField(choices=[('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')], default='pendiente', max_length=20, verbose_name='Estado de la solicitud')),
                ('reason', models.TextField(blank=True, verbose_name='Motivo de la solicitud')),
                ('beneficiary', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='data_deletion_requests', to='beneficiary.beneficiary', verbose_name='Beneficiario')),
            ],
            options={
                'verbose_name': 'Solicitud de eliminacion de datos',
                'verbose_name_plural': 'Solicitudes de eliminacion de datos',
                'ordering': ['-request_date'],
            },
        ),
    ]
