from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Beneficiary',
            fields=[
                ('id', models.CharField(max_length=200, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nombre')),
                ('location', models.CharField(max_length=300, verbose_name='Ubicación')),
                ('phone', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('email', models.EmailField(max_length=254, verbose_name='Correo electrónico')),
                ('date_register', models.DateField(auto_now_add=True, verbose_name='Fecha de registro')),
            ],
            options={
                'verbose_name': 'Beneficiario',
                'verbose_name_plural': 'Beneficiarios',
                'ordering': ['-date_register'],
            },
        ),
    ]