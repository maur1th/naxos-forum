# Generated by Django 4.2.13 on 2024-06-18 21:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0005_remove_post_markup'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='thread',
            new_name='forum_threa_categor_ad026b_idx',
            old_fields=('category', 'slug'),
        ),
    ]
