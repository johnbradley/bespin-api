# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-08-01 19:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0022_auto_20170801_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='share_group',
            field=models.ForeignKey(help_text='Users who will have job output shared with them', on_delete=django.db.models.deletion.CASCADE, to='data.ShareGroup'),
        ),
        migrations.AlterField(
            model_name='jobquestionnaire',
            name='share_group',
            field=models.ForeignKey(help_text='Users who will have job output shared with them', on_delete=django.db.models.deletion.CASCADE, to='data.ShareGroup'),
        ),
    ]