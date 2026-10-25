from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from hospital.models import *

class Command(BaseCommand):
    help="Create fictional hospital demo data and demo login accounts."
    def handle(self,*args,**options):
        departments=[]
        for name,location in [("Cardiology","Block A · Floor 2"),("Neurology","Block B · Floor 3"),("Orthopedics","Block A · Floor 1"),("Pediatrics","Block C · Floor 2"),("General Medicine","Block C · Floor 1")]:
            d,_=Department.objects.get_or_create(name=name,defaults={"location":location})
            departments.append(d)
        names=["Ananya Mehta","Rahul Verma","Priya Shah","Arjun Rao","Neha Kapoor","Karan Iyer","Mira Joshi","Dev Malhotra","Sana Khan","Vikram Das","Riya Nair","Kabir Sen","Ishita Roy","Nikhil Bose","Asha Menon"]
        employees=[]
        for i,name in enumerate(names):
            dept=departments[i%5]
            e,_=Employee.objects.get_or_create(employee_id=f"EMP-{100+i}",defaults={"name":f"Dr. {name}","sex":["Female","Male"][i%2],"department":dept,"job_title":"Doctor","working_hours":"09:00 AM – 04:00 PM"})
            employees.append(e)
        for i,d in enumerate(departments):
            d.manager=employees[i]; d.save(update_fields=["manager"])
        first_names=["Aarav","Aditi","Kabir","Meera","Ishaan","Diya","Rohan","Anaya","Vivaan","Tara","Reyansh","Myra","Arjun","Saanvi","Advik","Kiara","Neil","Ira","Veer","Avni"]
        last_names=["Sharma","Singh","Patel","Kumar","Reddy","Joshi","Nair","Kapoor","Das","Mehta"]
        demo_departments=[0,0,0,1,1,1,1,2,2,2,3,3,3,4,4,4,4,4,4,4]
        patients=[]
        for i in range(20):
            department_index=demo_departments[i]
            p,_=Patient.objects.get_or_create(patient_id=f"P-{1021+i}",defaults={"name":f"{first_names[i]} {last_names[i%len(last_names)]}","date_of_birth":date(1980+i%20,1+(i%12),1+(i%26)),"sex":["Female","Male"][i%2],"medical_history":["Asthma","Hypertension","Seasonal allergies","Type 2 diabetes","No known history"][i%5],"department":departments[department_index],"assigned_doctor":employees[department_index]})
            # Keep the demo cohort's department and assigned doctor aligned.
            p.department=departments[department_index]
            p.assigned_doctor=employees[department_index]
            p.save(update_fields=["department","assigned_doctor"])
            # Give the demo dashboard a useful, deterministic registration trend.
            # These are fictional seed records; each seeded run refreshes their dates.
            demo_date=timezone.now()-timedelta(days=(i*3+i//4)%7,hours=(i*5)%10)
            Patient.objects.filter(pk=p.pk).update(created_at=demo_date)
            patients.append(p)
        conditions=["Hypertension","Migraine","Knee injury","Asthma","Type 2 diabetes","Viral fever","Anemia","Back pain","Bronchitis","Allergic rhinitis"]
        for i in range(10):
            Diagnosis.objects.get_or_create(patient=patients[i],doctor=employees[i],condition=conditions[i],defaults={"diagnosed_on":timezone.localdate()-timedelta(days=i+1),"notes":"Demo record for clinical workflow."})
        test_names=["ECG","Blood Test","X-Ray","MRI","CBC","Ultrasound","Lipid Profile","CT Scan","Urine Analysis","Echocardiogram"]
        demo_test_names=["ECG","Blood Test","X-Ray","ECG","CBC","Blood Test","MRI","ECG","X-Ray","Ultrasound","Blood Test","ECG","CBC","Lipid Profile","X-Ray","MRI","ECG","Blood Test","CT Scan","ECG"]
        for i in range(20):
            test=Test.objects.filter(patient=patients[i],name__in=test_names).first()
            if test:
                test.name=demo_test_names[i]
                test.test_date=timezone.localdate()-timedelta(days=i%7)
                test.doctor=employees[i%15]
                test.status=["Pending","Completed","In Progress"][i%3]
                test.save(update_fields=["name","test_date","doctor","status"])
            else:
                Test.objects.create(patient=patients[i],name=demo_test_names[i],test_date=timezone.localdate()-timedelta(days=i%7),doctor=employees[i%15],status=["Pending","Completed","In Progress"][i%3])
        for i in range(10):
            SurgicalEquipment.objects.get_or_create(equipment_id=f"EQ-{101+i}",defaults={"name":["ECG Machine","Patient Monitor","Ultrasound Machine","Surgical Scissors","Pulse Oximeter"][i%5],"category":"Machine" if i%2==0 else "Tool","department":departments[i%5],"available":i%4!=0})
        store,_=MedicalStore.objects.get_or_create(name="Central Medical Store",defaults={"location":"Ground Floor · Wing B"})
        for i in range(10):
            Prescription.objects.get_or_create(patient=patients[i],doctor=employees[i],medicine=["Amlodipine","Paracetamol","Metformin","Cetirizine","Omeprazole"][i%5],defaults={"medical_store":store,"quantity":10,"status":["Pending","Dispensed","Completed"][i%3]})
        for i in range(10):
            person,_=Person.objects.get_or_create(name=f"{last_names[i]} {['Family Contact','Caregiver','Relative'][i%3]}",defaults={"phone":f"+91 90000 {10000+i:05d}"})
            Caretaker.objects.get_or_create(patient=patients[i],person=person,defaults={"relationship":["Spouse","Parent","Sibling","Child"][i%4],"is_primary":True})
        for username,password,role,employee in [("receptionist","Reception123!","Receptionist",None),("doctor","Doctor123!","Doctor",employees[0]),("admin","Admin123!","Admin",None)]:
            user,_=User.objects.get_or_create(username=username,defaults={"first_name":role})
            user.set_password(password); user.save()
            UserProfile.objects.update_or_create(user=user,defaults={"role":role,"employee":employee})
        self.stdout.write(self.style.SUCCESS("Seeded departments, staff, patients, care links, diagnoses, tests, equipment, prescriptions and demo users."))
