# Generated by Django 4.1.7 on 2024-07-28 02:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_customuser_height_customuser_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='bmi',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
