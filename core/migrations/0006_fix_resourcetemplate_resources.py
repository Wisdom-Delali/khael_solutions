"""
Remaps ResourceTemplates from the zero-cost seed resources to the real,
priced resources that already existed in the database.

For each seeded generic resource (unit_cost=0), we look for an existing
resource whose title contains the generic name and has a non-zero unit_cost.
If found we re-point the template and delete the duplicate seed resource
(only if it has no usage records or purchases tied to it).
"""
from django.db import migrations


# Maps seeded generic title → substring used to find the real resource
REMAP_HINTS = {
    'A4 Paper':       'A4 Paper',
    'Ink Cartridge':  'Ink Cartridge',
    'Network Cable':  'Network Cable',
    'RJ45 Connector': 'RJ45 Connector',
    'SD Card':        'SD Card',
}


def remap_forward(apps, schema_editor):
    Resource         = apps.get_model('core', 'Resource')
    ResourceTemplate = apps.get_model('core', 'ResourceTemplate')
    ResourceUsage    = apps.get_model('core', 'ResourceUsage')
    PurchaseResource = apps.get_model('core', 'PurchaseResource')

    for seed_title, hint in REMAP_HINTS.items():
        try:
            seed_resource = Resource.objects.get(title=seed_title, unit_cost=0)
        except Resource.DoesNotExist:
            continue  # already cleaned up or never created

        # Find a better-priced resource whose title contains the hint
        # Exclude the seed resource itself; prefer higher stock / lower id as tiebreak
        candidates = (
            Resource.objects
            .filter(title__icontains=hint, unit_cost__gt=0)
            .exclude(pk=seed_resource.pk)
            .order_by('id')
        )
        if not candidates.exists():
            continue  # no better option; leave template as-is

        real_resource = candidates.first()

        # Re-point every template that references the seed resource
        for tmpl in ResourceTemplate.objects.filter(resource=seed_resource):
            # Guard against unique_together clash (real resource already has a template for this service_type)
            if ResourceTemplate.objects.filter(
                service_type=tmpl.service_type, resource=real_resource
            ).exists():
                tmpl.delete()
            else:
                tmpl.resource = real_resource
                tmpl.save()

        # Delete the seed resource only if nothing else references it
        has_usage    = ResourceUsage.objects.filter(resource=seed_resource).exists()
        has_purchase = PurchaseResource.objects.filter(resource=seed_resource).exists()
        if not has_usage and not has_purchase:
            seed_resource.delete()


def remap_reverse(apps, schema_editor):
    # Not worth reversing — forward migration is idempotent enough
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_resourcetemplate_seed'),
    ]

    operations = [
        migrations.RunPython(remap_forward, remap_reverse),
    ]
