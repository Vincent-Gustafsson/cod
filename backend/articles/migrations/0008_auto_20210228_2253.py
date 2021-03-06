# Generated by Django 3.1.7 on 2021-02-28 21:53

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0007_auto_20210215_0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='slug',
            field=autoslug.fields.AutoSlugField(always_update=True, default=None, editable=False, null=True, populate_from='title', unique=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=autoslug.fields.AutoSlugField(always_update=True, default=None, editable=False, null=True, populate_from='name', unique=True),
        ),
    ]
