# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-06-11 20:00
from __future__ import unicode_literals

from django.db import migrations


def get_models(apps, src, dst):
    return (
        apps.get_model(src, 'DDSEndpoint'),
        apps.get_model(dst, 'DDSEndpoint'),
        apps.get_model(src, 'DDSUserCredential'),
        apps.get_model(dst, 'DDSUserCredential'),
    )

def migrate_data(apps, src, dst):
    src_endpoint, dst_endpoint, src_credential, dst_credential = get_models(apps, src, dst)

    # Copy the endpoints
    for endpoint in src_endpoint.objects.all():
        dst_endpoint.objects.create(
            name=endpoint.name,
            agent_key=endpoint.agent_key,
            api_root=endpoint.api_root,
        )
    # copy credentials
    for credential in src_credential.objects.all():
        # Look up the new endpoint
        endpoint = dst_endpoint.objects.get(name=credential.endpoint.name)
        dst_credential.objects.create(
            endpoint=endpoint,
            user=credential.user,
            token=credential.token,
            dds_id=credential.dds_id
        )


def dds_models_to_gcb_web_auth(apps, schema_editor):
    migrate_data(apps, 'data', 'gcb_web_auth')


def dds_models_to_data(apps, schema_editor):
    migrate_data(apps, 'gcb_web_auth', 'data')


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0048_auto_20180611_1534'),
        ('gcb_web_auth', '0004_auto_20180410_1609'),
    ]

    operations = [
        migrations.RunPython(dds_models_to_gcb_web_auth, reverse_code=dds_models_to_data)
    ]
