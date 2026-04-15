from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_client_receipt'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('service_type', models.CharField(
                    blank=True,
                    choices=[
                        ('printing',   'Printing Services'),
                        ('network_it', 'Network & IT'),
                        ('multimedia', 'Multimedia Production'),
                        ('general',    'General Services'),
                    ],
                    max_length=20,
                )),
                ('default_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('description_template', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.AddField(
            model_name='report',
            name='query_text',
            field=models.TextField(blank=True, default='', help_text='User-entered natural language query (custom queries only)'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='report',
            name='report_type',
            field=models.CharField(
                choices=[
                    ('weekly',       'Weekly Summary'),
                    ('on_demand',    'On-Demand Report'),
                    ('custom_query', 'Custom Query'),
                ],
                default='on_demand',
                max_length=20,
            ),
        ),
    ]
