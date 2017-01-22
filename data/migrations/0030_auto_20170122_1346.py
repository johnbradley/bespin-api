# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-01-22 13:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0029_jobddsoutputdirectoryanswer'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jobddsoutputdirectoryanswer',
            old_name='string',
            new_name='directory_name',
        ),
        migrations.AlterField(
            model_name='jobddsoutputdirectoryanswer',
            name='dds_user_credentials',
            field=models.ForeignKey(help_text='Credentials with access to this directory', on_delete=django.db.models.deletion.CASCADE, to='data.DDSUserCredential'),
        ),
        migrations.AlterField(
            model_name='jobddsoutputdirectoryanswer',
            name='project_id',
            field=models.CharField(help_text='uuid from DukeDS for the project containing our directory', max_length=255, null=True),
        ),
    ]
