# Generated manually to add store field to Feedback

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('retailops', '0003_customer_store_feedback_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='store',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='feedbacks',
                to='retailops.store',
                default=1  # Temporary default for migration
            ),
            preserve_default=False,
        ),
        migrations.RemoveIndex(
            model_name='feedback',
            name='idx_feedback_key',
        ),
        migrations.AddIndex(
            model_name='feedback',
            index=models.Index(
                fields=['store', 'customer', 'category_code', 'created_at'],
                name='idx_feedback_full_key'
            ),
        ),
    ]
