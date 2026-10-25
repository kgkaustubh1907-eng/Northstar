import re
from django.db.models import Q
from hospital.models import Department, Employee, Patient, Test, SurgicalEquipment, Diagnosis
from hospital.permissions import role_of

def visible_patients(user):
    qs=Patient.objects.all()
    if user is not None and role_of(user)=="Doctor": qs=qs.filter(assigned_doctor__user_profile__user=user)
    return qs

def patient_row(p): return {"id":p.pk,"patient_id":p.patient_id,"name":p.name,"age":p.age,"sex":p.sex}
def doctor_row(e): return {"id":e.pk,"employee_id":e.employee_id,"name":e.name,"department":e.department.name if e.department else "Unassigned","working_hours":e.working_hours}
def run_query(query,user=None):
    raw=query.strip(); q=raw.lower(); result_type="general_search"; results=[]; message="Here are the matching hospital records."
    m=re.search(r"(?:doctors?|employees?)\s+(?:work(?:ing)?\s+)?in\s+(.+?)[?.!]*$",q)
    if m:
        dept=m.group(1).strip(); result_type="doctor_search"
        results=[doctor_row(x) for x in Employee.objects.select_related("department").filter(department__name__icontains=dept,is_active=True)]
        message=f"Doctors in {dept.title()}"
    elif (m:=re.search(r"find\s+patient\s+(.+?)[?.!]*$",q)):
        result_type="patient_search"; results=[patient_row(x) for x in visible_patients(user).filter(Q(name__icontains=m.group(1))|Q(patient_id__icontains=m.group(1)))[:50]]
    elif (m:=re.search(r"tests?\s+for\s+(.+?)[?.!]*$",q)):
        result_type="test_search"; terms=m.group(1).strip()
        qs=Test.objects.select_related("patient","doctor").filter(patient__in=visible_patients(user)).filter(Q(patient__name__icontains=terms)|Q(patient__patient_id__icontains=terms))
        results=[{"id":x.pk,"test":x.name,"patient":x.patient.name,"date":str(x.test_date),"status":x.status,"doctor":x.doctor.name if x.doctor else None} for x in qs[:50]]
    elif (m:=re.search(r"who\s+manages\s+(.+?)[?.!]*$",q)):
        result_type="department_manager"; d=Department.objects.select_related("manager").filter(name__icontains=m.group(1).strip()).first()
        results=[{"department":d.name,"manager":d.manager.name if d.manager else "Not assigned"}] if d else []
    elif (m:=re.search(r"equipment\s+in\s+(.+?)[?.!]*$",q)):
        result_type="equipment_search"; qs=SurgicalEquipment.objects.select_related("department").filter(department__name__icontains=m.group(1).strip())
        results=[{"id":x.pk,"equipment_id":x.equipment_id,"name":x.name,"department":x.department.name,"available":x.available} for x in qs]
    elif (m:=re.search(r"working\s+hours\s+(?:of|for)\s+(.+?)[?.!]*$",q)):
        result_type="working_hours"; qs=Employee.objects.filter(name__icontains=m.group(1).strip())
        results=[{"name":x.name,"working_hours":x.working_hours or "Not listed","department":x.department.name if x.department else None} for x in qs]
    elif "how many patients" in q or "patient count" in q:
        result_type="patient_count"; results=[{"total":visible_patients(user).count()}]; message="Current registered patient count"
    elif (m:=re.search(r"patients?\s+diagnosed\s+with\s+(.+?)[?.!]*$",q)):
        result_type="diagnosis_search"; qs=visible_patients(user).filter(diagnoses__condition__icontains=m.group(1).strip()).distinct()
        results=[patient_row(x) for x in qs[:50]]
    else:
        # Friendly broad search lets the query center handle common names and IDs.
        term=raw
        results += [{"id":p.pk,"kind":"Patient","label":p.name,"subtitle":p.patient_id,"url":f"/patients/{p.pk}"} for p in visible_patients(user).filter(Q(name__icontains=term)|Q(patient_id__icontains=term))[:8]]
        results += [{"id":e.pk,"kind":"Employee","label":e.name,"subtitle":e.department.name if e.department else "Employee","url":"/doctors"} for e in Employee.objects.select_related("department").filter(Q(name__icontains=term)|Q(employee_id__icontains=term))[:8]]
        results += [{"id":d.pk,"kind":"Department","label":d.name,"subtitle":d.location,"url":"/departments"} for d in Department.objects.filter(name__icontains=term)[:8]]
    return {"query":raw,"type":result_type,"message":message,"results":results}
