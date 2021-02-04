# Generated by Django 3.1.5 on 2021-02-04 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='saved_articles',
            field=models.ManyToManyField(blank=True, related_name='saves', to='articles.Article'),
        ),
    ]
