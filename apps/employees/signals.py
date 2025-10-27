from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models.employee import (
    Employee, Direction, Division, Service, Departement, Filiere, Grade, Position
)
from .cache import (
    invalidate_employee_cache,
    invalidate_org_cache,
    invalidate_taxonomy_cache,
    invalidate_user_cache,
)


@receiver(post_save, sender=Employee)
def employee_saved(sender, instance, created, **kwargs):
    # Invalidate employee caches
    invalidate_employee_cache(employee_id=instance.pk)
    if instance.user_id:
        invalidate_user_cache(instance.user_id)


@receiver(post_delete, sender=Employee)
def employee_deleted(sender, instance, **kwargs):
    invalidate_employee_cache(employee_id=instance.pk)
    if instance.user_id:
        invalidate_user_cache(instance.user_id)


# Organizational models invalidate org cache
@receiver(post_save, sender=Direction)
@receiver(post_save, sender=Division)
@receiver(post_save, sender=Service)
@receiver(post_save, sender=Departement)
@receiver(post_save, sender=Filiere)
def org_saved(sender, instance, created, **kwargs):
    invalidate_org_cache()


@receiver(post_delete, sender=Direction)
@receiver(post_delete, sender=Division)
@receiver(post_delete, sender=Service)
@receiver(post_delete, sender=Departement)
@receiver(post_delete, sender=Filiere)
def org_deleted(sender, instance, **kwargs):
    invalidate_org_cache()


# Taxonomy invalidation
@receiver(post_save, sender=Grade)
@receiver(post_save, sender=Position)
def taxonomy_saved(sender, instance, created, **kwargs):
    invalidate_taxonomy_cache()


@receiver(post_delete, sender=Grade)
@receiver(post_delete, sender=Position)
def taxonomy_deleted(sender, instance, **kwargs):
    invalidate_taxonomy_cache()
