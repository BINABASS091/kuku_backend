# Generated manually to update models for PostgreSQL schema compatibility

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sensors', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sensortype',
            old_name='id',
            new_name='sensorTypeID',
        ),
        migrations.RenameField(
            model_name='reading',
            old_name='id',
            new_name='readingID',
        ),
        migrations.AlterField(
            model_name='reading',
            name='sensor_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='readings', to='sensors.sensortype'),
        ),
    ]
