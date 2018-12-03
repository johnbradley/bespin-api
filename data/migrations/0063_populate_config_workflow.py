# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-11-14 19:24
from __future__ import unicode_literals

from django.db import migrations


def populate_workflow_fields(apps, schema_editor):
    WorkflowConfiguration = apps.get_model("data", "WorkflowConfiguration")
    for obj in WorkflowConfiguration.objects.all():
        obj.workflow = obj.workflow_version.workflow
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0062_add_workflow_to_configuration'),
    ]

    operations = [
        migrations.RunPython(populate_workflow_fields, migrations.RunPython.noop),
    ]
