# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2016-10-21 23:30
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='threads', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='thread',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='threads', to='forum.Category'),
        ),
        migrations.AddField(
            model_name='thread',
            name='contributors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='forum.Thread'),
        ),
        migrations.AddField(
            model_name='pollquestion',
            name='thread',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='question', to='forum.Thread'),
        ),
        migrations.AddField(
            model_name='pollquestion',
            name='voters',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pollchoice',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='forum.PollQuestion'),
        ),
        migrations.AlterIndexTogether(
            name='thread',
            index_together=set([('category', 'slug')]),
        ),
    ]