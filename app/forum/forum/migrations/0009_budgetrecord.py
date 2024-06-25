# Generated by Django 4.2.13 on 2024-06-22 18:31

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0008_alter_usermentions_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.FloatField()),
                ('label', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ['pk'],
            },
        ),
    ]