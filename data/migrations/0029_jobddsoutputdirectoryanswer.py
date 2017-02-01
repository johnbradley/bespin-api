# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-01-21 20:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0028_auto_20170121_2015'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobDDSOutputDirectoryAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_id', models.CharField(help_text='uuid from DukeDS for the project containing our file', max_length=255, null=True)),
                ('string', models.CharField(help_text='name of the directory to create', max_length=255, null=True)),
                ('answer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='dds_output_directory', to='data.JobAnswer')),
                ('dds_user_credentials', models.ForeignKey(help_text='Credentials with access to this file', on_delete=django.db.models.deletion.CASCADE, to='data.DDSUserCredential')),
            ],
        ),
    ]