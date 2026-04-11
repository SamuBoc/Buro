import cases.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('beneficiary', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(editable=False, max_length=20, unique=True, verbose_name='Codigo')),
                ('sala', models.CharField(choices=[('civil', 'Civil'), ('laboral', 'Laboral'), ('penal', 'Penal'), ('publico', 'Publico'), ('familia', 'Familia')], max_length=20, verbose_name='Sala juridica')),
                ('description', models.TextField(verbose_name='Descripcion del problema')),
                ('state', models.CharField(default='Registrado - Pendiente asignacion', max_length=100, verbose_name='Estado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creacion')),
                ('beneficiary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cases', to='beneficiary.beneficiary', verbose_name='Beneficiario')),
            ],
            options={
                'verbose_name': 'Caso',
                'verbose_name_plural': 'Casos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CaseDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=cases.models.case_document_upload_path, verbose_name='Archivo')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de carga')),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='cases.case', verbose_name='Caso')),
            ],
            options={
                'verbose_name': 'Documento del caso',
                'verbose_name_plural': 'Documentos del caso',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
