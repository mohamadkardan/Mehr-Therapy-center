# Generated by Django 5.1.4 on 2024-12-16 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_center_client_owner_therapist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('client', 'مراجع'), ('therapist', 'مشاور'), ('center', 'مرکز'), ('owner', 'ادمین اصلی')], default='client', max_length=20),
        ),
    ]