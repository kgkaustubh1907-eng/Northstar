from datetime import date
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from .models import Department, Employee, Patient, UserProfile, SurgicalEquipment

class HospitalWorkflowTests(APITestCase):
    def setUp(self):
        self.department=Department.objects.create(name="Cardiology",location="Block A · Floor 2")
        self.doctor=Employee.objects.create(employee_id="EMP-TEST-1",name="Dr. Ananya Mehta",department=self.department,working_hours="09:00 AM – 04:00 PM")
        receptionist=User.objects.create_user("reception-test",password="Reception123!")
        UserProfile.objects.create(user=receptionist,role=UserProfile.Role.RECEPTIONIST)
        doctor=User.objects.create_user("doctor-test",password="Doctor123!")
        UserProfile.objects.create(user=doctor,role=UserProfile.Role.DOCTOR,employee=self.doctor)
        admin=User.objects.create_superuser("admin-test",email="admin@example.invalid",password="Admin123!")
        self.receptionist=receptionist
        self.doctor_user=doctor
        self.admin=admin

    def authenticate(self,user):
        self.client.force_authenticate(user=user)

    def test_receptionist_patient_registration_updates_dashboard_and_query(self):
        self.authenticate(self.receptionist)
        response=self.client.post("/api/patients/",{"name":"Aarav Sharma","date_of_birth":"1995-05-12","sex":"Male","medical_history":"Asthma","department":self.department.pk},format="json")
        self.assertEqual(response.status_code,201)
        self.assertTrue(response.data["patient_id"].startswith("P-"))
        self.assertEqual(self.client.get("/api/dashboard/").data["total_patients"],1)
        found=self.client.post("/api/query/",{"query":"Find patient Aarav Sharma"},format="json")
        self.assertEqual(found.status_code,200)
        self.assertEqual(found.data["results"][0]["patient_id"],response.data["patient_id"])

    def test_receptionist_can_add_diagnosis_and_test_but_not_equipment(self):
        patient=Patient.objects.create(name="Demo Patient",date_of_birth=date(1990,1,1),department=self.department,assigned_doctor=self.doctor)
        self.authenticate(self.receptionist)
        diagnosis=self.client.post("/api/diagnoses/",{"patient":patient.pk,"doctor":self.doctor.pk,"condition":"Hypertension"},format="json")
        test=self.client.post("/api/tests/",{"patient":patient.pk,"doctor":self.doctor.pk,"name":"ECG","status":"Pending"},format="json")
        self.assertEqual(diagnosis.status_code,201)
        self.assertEqual(test.status_code,201)
        self.assertEqual(self.client.post("/api/equipment/",{},format="json").status_code,403)

    def test_doctor_is_limited_to_assigned_patients_and_can_record_diagnosis(self):
        patient=Patient.objects.create(name="Assigned Patient",date_of_birth=date(1985,2,1),department=self.department,assigned_doctor=self.doctor)
        self.authenticate(self.doctor_user)
        listing=self.client.get("/api/patients/")
        self.assertEqual(listing.status_code,200)
        self.assertEqual([p["id"] for p in listing.data["results"]],[patient.pk])
        diagnosis=self.client.post("/api/diagnoses/",{"patient":patient.pk,"condition":"Migraine"},format="json")
        self.assertEqual(diagnosis.status_code,201)
        self.assertEqual(diagnosis.data["doctor"],self.doctor.pk)
        other=Employee.objects.create(employee_id="EMP-TEST-2",name="Dr. Other Clinician",department=self.department)
        outside=Patient.objects.create(name="Other Assigned Patient",date_of_birth=date(1991,3,1),department=self.department,assigned_doctor=other)
        self.assertEqual(self.client.post("/api/diagnoses/",{"patient":outside.pk,"condition":"Restricted"},format="json").status_code,403)
        result=self.client.post("/api/query/",{"query":"Find patient Other Assigned Patient"},format="json")
        self.assertEqual(result.data["results"],[])
        self.assertEqual(self.client.post("/api/patients/",{"name":"Forbidden","date_of_birth":"1990-01-01"},format="json").status_code,403)

    def test_admin_can_manage_equipment(self):
        self.authenticate(self.admin)
        response=self.client.post("/api/equipment/",{"equipment_id":"EQ-TEST-1","name":"ECG Machine","category":"Machine","department":self.department.pk,"available":True},format="json")
        self.assertEqual(response.status_code,201)
        equipment_id=response.data["id"]
        self.assertEqual(self.client.patch(f"/api/equipment/{equipment_id}/",{"available":False},format="json").status_code,200)
        self.assertEqual(self.client.delete(f"/api/equipment/{equipment_id}/").status_code,204)
