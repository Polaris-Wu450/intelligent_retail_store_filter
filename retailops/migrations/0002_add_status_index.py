from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('retailops', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionplan',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20),
        ),
        migrations.AddIndex(
            model_name='actionplan',
            index=models.Index(fields=['status', 'created_at'], name='idx_status_created'),
        ),
    ]
