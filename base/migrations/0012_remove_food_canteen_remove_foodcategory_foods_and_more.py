# Generated by Django 4.1.7 on 2024-07-28 05:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_foodcategory_foods_remove_food_category_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='food',
            name='canteen',
        ),
        migrations.RemoveField(
            model_name='foodcategory',
            name='foods',
        ),
        migrations.AddField(
            model_name='foodcategory',
            name='canteen',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='base.canteen'),
        ),
        migrations.RemoveField(
            model_name='food',
            name='category',
        ),
        migrations.AddField(
            model_name='food',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='foods', to='base.foodcategory'),
        ),
    ]