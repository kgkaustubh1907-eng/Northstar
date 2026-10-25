from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from uuid import uuid4

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    manager = models.OneToOneField("Employee", null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_department")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Employee(models.Model):
    class Sex(models.TextChoices):
        MALE="Male"; FEMALE="Female"; OTHER="Other"; UNSPECIFIED="Unspecified"
    employee_id = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=140, db_index=True)
    sex = models.CharField(max_length=16, choices=Sex.choices, default=Sex.UNSPECIFIED)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees")
    job_title = models.CharField(max_length=100, default="Doctor")
    working_hours = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.name} ({self.employee_id})"

class Patient(models.Model):
    class Sex(models.TextChoices):
        MALE="Male"; FEMALE="Female"; OTHER="Other"; UNSPECIFIED="Unspecified"
    patient_id = models.CharField(max_length=24, unique=True, blank=True)
    name = models.CharField(max_length=140, db_index=True)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=16, choices=Sex.choices, default=Sex.UNSPECIFIED)
    medical_history = models.TextField(blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="patients")
    assigned_doctor = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_patients")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["name", "patient_id"])]
    def save(self, *args, **kwargs):
        if not self.patient_id: self.patient_id = f"P-{uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    @property
    def age(self):
        today = timezone.localdate()
        return today.year-self.date_of_birth.year-((today.month,today.day)<(self.date_of_birth.month,self.date_of_birth.day))
    def clean(self):
        if self.date_of_birth and self.date_of_birth > timezone.localdate(): raise ValidationError({"date_of_birth":"Date of birth cannot be in the future."})
    def __str__(self): return f"{self.name} ({self.patient_id})"

class Person(models.Model):
    name = models.CharField(max_length=140, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    medical_history = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    def __str__(self): return self.name

class Caretaker(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="caretaker_links")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="cared_for_patients")
    relationship = models.CharField(max_length=60)
    is_primary = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["patient","person"], name="unique_patient_caretaker")]

class Diagnosis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="diagnoses")
    doctor = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="diagnoses")
    condition = models.CharField(max_length=180, db_index=True)
    diagnosed_on = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-diagnosed_on"]

class Test(models.Model):
    class Status(models.TextChoices):
        PENDING="Pending"; IN_PROGRESS="In Progress"; COMPLETED="Completed"; CANCELLED="Cancelled"
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="tests")
    doctor = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name="ordered_tests")
    name = models.CharField(max_length=140, db_index=True)
    test_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-test_date"]

class MedicalStore(models.Model):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=160, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    def __str__(self): return self.name

class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING="Pending"; DISPENSED="Dispensed"; COMPLETED="Completed"
    prescription_id = models.CharField(max_length=24, unique=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions")
    doctor = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="prescriptions")
    medicine = models.CharField(max_length=160)
    medical_store = models.ForeignKey(MedicalStore, null=True, blank=True, on_delete=models.SET_NULL, related_name="prescriptions")
    quantity = models.PositiveIntegerField(default=1)
    prescribed_on = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    instructions = models.TextField(blank=True)
    def save(self, *args, **kwargs):
        if not self.prescription_id: self.prescription_id = f"RX-{uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

class SurgicalEquipment(models.Model):
    class Category(models.TextChoices):
        MACHINE="Machine"; TOOL="Tool"
    equipment_id = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=140, db_index=True)
    category = models.CharField(max_length=16, choices=Category.choices)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="equipment")
    available = models.BooleanField(default=True)
    acquired_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.name} ({self.equipment_id})"

class UserProfile(models.Model):
    class Role(models.TextChoices):
        RECEPTIONIST="Receptionist"; DOCTOR="Doctor"; ADMIN="Admin"
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.RECEPTIONIST)
    employee = models.OneToOneField(Employee, null=True, blank=True, on_delete=models.SET_NULL, related_name="user_profile")
    def __str__(self): return f"{self.user.username} — {self.role}"

class DataRevision(models.Model):
    """Monotonic change marker polled by open clients for cross-device updates."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    revision = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(default=timezone.now)
