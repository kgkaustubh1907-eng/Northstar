from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from .models import (
    Caretaker,
    Department,
    Diagnosis,
    Employee,
    MedicalStore,
    Patient,
    Person,
    Prescription,
    SurgicalEquipment,
    Test,
    UserProfile,
    DataRevision,
)


TRACKED_MODELS = (
    Caretaker,
    Department,
    Diagnosis,
    Employee,
    MedicalStore,
    Patient,
    Person,
    Prescription,
    SurgicalEquipment,
    Test,
    UserProfile,
)


def bump_revision(sender, **kwargs):
    DataRevision.objects.filter(pk=1).update(
        revision=F("revision") + 1,
        updated_at=timezone.now(),
    )


for model in TRACKED_MODELS:
    post_save.connect(bump_revision, sender=model, dispatch_uid=f"hospital_revision_save_{model.__name__}")
    post_delete.connect(bump_revision, sender=model, dispatch_uid=f"hospital_revision_delete_{model.__name__}")
