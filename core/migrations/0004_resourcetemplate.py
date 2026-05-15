from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_jobtype_report_querytext'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.CharField(
                    choices=[
                        ('printing',   'Printing Services'),
                        ('network_it', 'Network & IT'),
                        ('multimedia', 'Multimedia Production'),
                        ('general',    'General Services'),
                    ],
                    max_length=20,
                )),
                ('default_quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ('resource', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='templates',
                    to='core.resource',
                )),
            ],
            options={
                'ordering': ['service_type', 'resource__title'],
                'unique_together': {('service_type', 'resource')},
            },
        ),
    ]
