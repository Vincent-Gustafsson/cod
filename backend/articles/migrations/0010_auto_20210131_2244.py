# Generated by Django 3.1.5 on 2021-01-31 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0009_auto_20210131_2242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='description',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]