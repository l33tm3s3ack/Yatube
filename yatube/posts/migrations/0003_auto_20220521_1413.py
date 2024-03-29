# Generated by Django 2.2.19 on 2022-05-21 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220521_1358'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='desciption',
            new_name='description',
        ),
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.CharField(max_length=30, unique=True),
        ),
        migrations.AlterField(
            model_name='group',
            name='title',
            field=models.CharField(max_length=30),
        ),
    ]
