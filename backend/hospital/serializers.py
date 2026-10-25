from rest_framework import serializers
from .models import *

class PatientSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    caretaker = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True)
    doctor_name = serializers.CharField(source="assigned_doctor.name", read_only=True)
    class Meta:
        model = Patient
        fields = ["id","patient_id","name","date_of_birth","age","sex","medical_history","department","department_name","assigned_doctor","doctor_name","caretaker","created_at","updated_at"]
        read_only_fields = ["patient_id","created_at","updated_at"]
    def get_caretaker(self, obj):
        link = obj.caretaker_links.select_related("person").filter(is_primary=True).first()
        return {"id":link.person_id,"name":link.person.name,"relationship":link.relationship} if link else None
    def validate_date_of_birth(self, value):
        from django.utils import timezone
        if value > timezone.localdate(): raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    class Meta:
        model = Employee
        fields = "__all__"

class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.name", read_only=True)
    doctors_count = serializers.SerializerMethodField()
    equipment_count = serializers.IntegerField(source="equipment.count", read_only=True)
    class Meta:
        model = Department
        fields = "__all__"
    def get_doctors_count(self,obj): return obj.employees.filter(job_title__icontains="doctor").count()

class DiagnosisSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_id = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    class Meta:
        model = Diagnosis
        fields = "__all__"

class TestSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True, allow_null=True)
    class Meta:
        model = Test
        fields = "__all__"

class EquipmentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    class Meta:
        model = SurgicalEquipment
        fields = "__all__"

class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    store_name = serializers.CharField(source="medical_store.name", read_only=True, allow_null=True)
    class Meta:
        model = Prescription
        fields = "__all__"
        read_only_fields = ["prescription_id"]

class MedicalStoreSerializer(serializers.ModelSerializer):
    prescription_count = serializers.IntegerField(source="prescriptions.count", read_only=True)
    class Meta:
        model = MedicalStore
        fields = "__all__"

class PersonSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    class Meta:
        model = Person
        fields = "__all__"
    def get_age(self,obj):
        if not obj.date_of_birth: return None
        from django.utils import timezone
        today=timezone.localdate()
        return today.year-obj.date_of_birth.year-((today.month,today.day)<(obj.date_of_birth.month,obj.date_of_birth.day))
    def validate_date_of_birth(self,value):
        from django.utils import timezone
        if value and value>timezone.localdate(): raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

class CaretakerSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source="person.name", read_only=True)
    person_date_of_birth = serializers.DateField(source="person.date_of_birth", read_only=True, allow_null=True)
    person_medical_history = serializers.CharField(source="person.medical_history", read_only=True)
    person_phone = serializers.CharField(source="person.phone", read_only=True)
    person_age = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    class Meta:
        model = Caretaker
        fields = ["id","patient","person","relationship","is_primary","person_name","person_date_of_birth","person_age","person_medical_history","person_phone","patient_name","patient_code"]
    def get_person_age(self,obj):
        if not obj.person.date_of_birth:return None
        from django.utils import timezone
        today=timezone.localdate(); dob=obj.person.date_of_birth
        return today.year-dob.year-((today.month,today.day)<(dob.month,dob.day))
