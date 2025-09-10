# Generated manually to update models for PostgreSQL schema compatibility

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('breeds', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='breedtype',
            old_name='id',
            new_name='breed_typeID',
        ),
        migrations.RenameField(
            model_name='breedtype',
            old_name='name',
            new_name='breedType',
        ),
        migrations.RenameField(
            model_name='breed',
            old_name='id',
            new_name='breedID',
        ),
        migrations.RenameField(
            model_name='breed',
            old_name='name',
            new_name='breedName',
        ),
        migrations.RenameField(
            model_name='breed',
            old_name='photo',
            new_name='preedphoto',
        ),
        migrations.RenameField(
            model_name='breed',
            old_name='type',
            new_name='breed_typeID',
        ),
        migrations.RenameField(
            model_name='activitytype',
            old_name='id',
            new_name='activityTypeID',
        ),
        migrations.RenameField(
            model_name='activitytype',
            old_name='name',
            new_name='activityType',
        ),
        migrations.RenameField(
            model_name='breedactivity',
            old_name='id',
            new_name='breedActivityID',
        ),
        migrations.RenameField(
            model_name='breedactivity',
            old_name='breed',
            new_name='breedID',
        ),
        migrations.RenameField(
            model_name='breedactivity',
            old_name='activity_type',
            new_name='activityTypeID',
        ),
        migrations.RenameField(
            model_name='conditiontype',
            old_name='id',
            new_name='condition_typeID',
        ),
        migrations.RenameField(
            model_name='breedcondition',
            old_name='id',
            new_name='breed_conditionID',
        ),
        migrations.RenameField(
            model_name='breedcondition',
            old_name='breed',
            new_name='breedID',
        ),
        migrations.RenameField(
            model_name='breedcondition',
            old_name='condition_type',
            new_name='condition_typeID',
        ),
        migrations.RenameField(
            model_name='foodtype',
            old_name='id',
            new_name='foodTypeID',
        ),
        migrations.RenameField(
            model_name='breedfeeding',
            old_name='id',
            new_name='breedFeedingID',
        ),
        migrations.RenameField(
            model_name='breedfeeding',
            old_name='breed',
            new_name='breedID',
        ),
        migrations.RenameField(
            model_name='breedfeeding',
            old_name='food_type',
            new_name='foodTypeID',
        ),
        migrations.RenameField(
            model_name='breedgrowth',
            old_name='id',
            new_name='breedGrowthID',
        ),
        migrations.RenameField(
            model_name='breedgrowth',
            old_name='breed',
            new_name='breedID',
        ),
    ]
