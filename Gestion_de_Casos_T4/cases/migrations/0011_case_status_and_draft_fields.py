from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0010_case_rejection_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='status',
            field=models.CharField(
                choices=[('borrador', 'Borrador'), ('completo', 'Completo')],
                default='completo',
                max_length=20,
                verbose_name='Estado del formulario',
            ),
        ),
        migrations.AlterField(
            model_name='case',
            name='beneficiary',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name='cases',
                to='beneficiary.beneficiary',
                verbose_name='Beneficiario',
            ),
        ),
        migrations.AlterField(
            model_name='case',
            name='description',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Descripcion del problema',
            ),
        ),
        migrations.AlterField(
            model_name='case',
            name='sala',
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
                verbose_name='Sala juridica',
            ),
        ),
    ]
