from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0004_caseevaluation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caseevaluation',
            name='score',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=3,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(5),
                ],
                verbose_name='Puntaje',
            ),
        ),
    ]
