# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-04-18 20:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0002_auto_20170418_2011'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='workflowversion',
            options={'ordering': ['version']},
        ),
        migrations.AlterUniqueTogether(
            name='workflowversion',
            unique_together=set([('workflow', 'version')]),
        ),
    ]
