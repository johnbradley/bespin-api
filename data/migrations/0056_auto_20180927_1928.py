# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-09-27 19:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0055_auto_20180831_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='vm_volume_mounts',
            field=models.TextField(default='{"/dev/vdb1": "/work"}', help_text='JSON-encoded dictionary of volume mounts, e.g. {"/dev/vdb1": "/work"}'),
        ),
        migrations.AlterField(
            model_name='jobanswerset',
            name='user_job_order_json',
            field=models.TextField(blank=True, default='{}', help_text='JSON containing the portion of the job order specified by user'),
        ),
        migrations.AlterField(
            model_name='jobquestionnaire',
            name='volume_mounts',
            field=models.TextField(default='{"/dev/vdb1": "/work"}', help_text='JSON-encoded dictionary of volume mounts, e.g. {"/dev/vdb1": "/work"}'),
        ),
    ]
