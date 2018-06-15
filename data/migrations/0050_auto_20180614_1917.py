# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-06-14 19:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0049_dds_endpoint_credential_to_gcb_web_auth'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ddsusercredential',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='ddsusercredential',
            name='endpoint',
        ),
        migrations.RemoveField(
            model_name='ddsusercredential',
            name='user',
        ),
        migrations.AlterField(
            model_name='ddsjobinputfile',
            name='dds_user_credentials',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gcb_web_auth.DDSUserCredential'),
        ),
        migrations.AlterField(
            model_name='jobddsoutputproject',
            name='dds_user_credentials',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='gcb_web_auth.DDSUserCredential'),
        ),
        migrations.DeleteModel(
            name='DDSEndpoint',
        ),
        migrations.DeleteModel(
            name='DDSUserCredential',
        ),
    ]
