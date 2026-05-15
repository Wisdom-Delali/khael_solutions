from decimal import Decimal
from django.db import migrations

SEED = [
    # (service_type, resource_title, unit, default_quantity)
    ('printing',   'A4 Paper',        'reams',   Decimal('5')),
    ('printing',   'Ink Cartridge',   'units',   Decimal('2')),
    ('network_it', 'Network Cable',   'metres',  Decimal('10')),
    ('network_it', 'RJ45 Connector',  'units',   Decimal('20')),
    ('multimedia', 'SD Card',         'units',   Decimal('1')),
    ('multimedia', 'External Flash',  'units',   Decimal('1')),
    ('general',    'A4 Paper',        'reams',   Decimal('2')),
    ('general',    'Ballpoint Pen',   'units',   Decimal('5')),
]


def seed_forward(apps, schema_editor):
    Resource = apps.get_model('core', 'Resource')
    ResourceTemplate = apps.get_model('core', 'ResourceTemplate')
    for service_type, title, unit, qty in SEED:
        resource, _ = Resource.objects.get_or_create(
            title=title,
            defaults={'unit': unit, 'quantity': 0, 'unit_cost': 0, 'reorder_level': 10},
        )
        ResourceTemplate.objects.get_or_create(
            service_type=service_type,
            resource=resource,
            defaults={'default_quantity': qty},
        )


def seed_reverse(apps, schema_editor):
    apps.get_model('core', 'ResourceTemplate').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_resourcetemplate'),
    ]

    operations = [
        migrations.RunPython(seed_forward, seed_reverse),
    ]
