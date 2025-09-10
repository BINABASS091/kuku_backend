# Generated manually to update models for PostgreSQL schema compatibility

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='farm',
            old_name='id',
            new_name='farmID',
        ),
        migrations.RenameField(
            model_name='device',
            old_name='id',
            new_name='deviceID',
        ),
    ]
