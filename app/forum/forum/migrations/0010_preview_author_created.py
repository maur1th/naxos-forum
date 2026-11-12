from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0009_budgetrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='preview',
            name='author',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='preview',
            name='created',
            field=models.DateTimeField(
                default=django.utils.timezone.now),
        ),
    ]
