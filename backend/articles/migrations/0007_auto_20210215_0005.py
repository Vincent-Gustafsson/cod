# Generated by Django 3.1.5 on 2021-02-14 23:05

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0006_article_thumbnail'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='article',
            managers=[
                ('_all_articles', django.db.models.manager.Manager()),
            ],
        ),
    ]
