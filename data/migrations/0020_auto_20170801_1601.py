# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-08-01 16:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0019_auto_20170714_1302'),
    ]

    operations = [
        migrations.CreateModel(
            name='DDSUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the user', max_length=255)),
                ('dds_id', models.CharField(help_text='Unique ID assigned to the user in DukeDS', max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='ShareGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of this group', max_length=255)),
                ('users', models.ManyToManyField(help_text='Users that belong to this group', to='data.DDSUser')),
            ],
        ),
        migrations.AddField(
            model_name='job',
            name='share_group',
            field=models.OneToOneField(help_text='Users who will have job output shared with them', null=True, on_delete=django.db.models.deletion.CASCADE, to='data.ShareGroup'),
        ),
        migrations.AddField(
            model_name='jobquestionnaire',
            name='share_group',
            field=models.OneToOneField(help_text='Users who will have job output shared with them', null=True, on_delete=django.db.models.deletion.CASCADE, to='data.ShareGroup'),
        ),
    ]