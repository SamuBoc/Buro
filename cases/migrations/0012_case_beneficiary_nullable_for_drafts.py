import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beneficiary", "0006_encrypt_sensitive_fields"),
        ("cases", "0011_merge_20260524_2359"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="beneficiary",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cases",
                to="beneficiary.beneficiary",
                verbose_name="Beneficiario",
            ),
        ),
    ]
