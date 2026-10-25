from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import *
from .serializers import *
from .permissions import HospitalPermission, role_of
from .services.query_service import run_query

@api_view(["POST"])
@permission_classes([])
def login(request):
    user=authenticate(request,username=request.data.get("username", ""),password=request.data.get("password", ""))
    if not user or not user.is_active: return Response({"detail":"Invalid username or password."},status=status.HTTP_401_UNAUTHORIZED)
    token,_=Token.objects.get_or_create(user=user)
    return Response({"access":token.key,"refresh":token.key})

class HospitalViewSet(viewsets.ModelViewSet):
    permission_classes = [HospitalPermission]
    def filter_queryset(self, queryset):
        queryset=super().filter_queryset(queryset)
        params=self.request.query_params
        patient=params.get("patient")
        department=params.get("department")
        if patient and hasattr(queryset.model,"patient_id"): queryset=queryset.filter(patient_id=patient)
        if department and hasattr(queryset.model,"department_id"): queryset=queryset.filter(department_id=department)
        if params.get("sex") and hasattr(queryset.model,"sex"): queryset=queryset.filter(sex=params["sex"])
        if params.get("status") and hasattr(queryset.model,"status"): queryset=queryset.filter(status=params["status"])
        if params.get("category") and hasattr(queryset.model,"category"): queryset=queryset.filter(category=params["category"])
        if params.get("available") in ("true","false") and hasattr(queryset.model,"available"): queryset=queryset.filter(available=params["available"]=="true")
        return queryset

class PatientViewSet(HospitalViewSet):
    queryset=Patient.objects.select_related("department","assigned_doctor").prefetch_related("caretaker_links__person","diagnoses__doctor","tests__doctor","prescriptions__doctor")
    serializer_class=PatientSerializer
    search_fields=["name","patient_id","medical_history"]
    ordering_fields=["name","created_at","date_of_birth"]
    def get_queryset(self):
        qs=super().get_queryset()
        if role_of(self.request.user)=="Doctor": qs=qs.filter(assigned_doctor__user_profile__user=self.request.user)
        return qs
    @action(detail=True, methods=["get"])
    def history(self,request,pk=None):
        patient=self.get_object()
        return Response({"diagnoses":DiagnosisSerializer(patient.diagnoses.select_related("doctor"),many=True).data,
            "tests":TestSerializer(patient.tests.select_related("doctor"),many=True).data,
            "prescriptions":PrescriptionSerializer(patient.prescriptions.select_related("doctor","medical_store"),many=True).data,
            "caretakers":CaretakerSerializer(patient.caretaker_links.select_related("person"),many=True).data})

class EmployeeViewSet(HospitalViewSet):
    queryset=Employee.objects.select_related("department").all().order_by("name"); serializer_class=EmployeeSerializer
    search_fields=["name","employee_id","department__name"]; ordering_fields=["name","employee_id"]
    def get_queryset(self):
        qs=super().get_queryset()
        if role_of(self.request.user)=="Doctor": qs=qs.filter(user_profile__user=self.request.user)
        return qs

class DepartmentViewSet(HospitalViewSet):
    queryset=Department.objects.select_related("manager").prefetch_related("employees","equipment").order_by("name"); serializer_class=DepartmentSerializer
    search_fields=["name","location"]; ordering_fields=["name"]
    @action(detail=True,methods=["get"])
    def detail_data(self,request,pk=None):
        dept=self.get_object()
        return Response({"department":DepartmentSerializer(dept).data,"employees":EmployeeSerializer(dept.employees.all(),many=True).data,"equipment":EquipmentSerializer(dept.equipment.all(),many=True).data})

class DiagnosisViewSet(HospitalViewSet):
    queryset=Diagnosis.objects.select_related("patient","doctor").all(); serializer_class=DiagnosisSerializer
    search_fields=["condition","patient__name","patient__patient_id","doctor__name"]; ordering_fields=["diagnosed_on"]
    def get_serializer(self,*args,**kwargs):
        serializer=super().get_serializer(*args,**kwargs)
        if role_of(self.request.user)=="Doctor": serializer.fields["doctor"].required=False
        return serializer
    def get_queryset(self):
        qs=super().get_queryset()
        if role_of(self.request.user)=="Doctor": qs=qs.filter(doctor__user_profile__user=self.request.user)
        return qs
    def perform_create(self,serializer):
        if role_of(self.request.user)=="Doctor":
            employee=self.request.user.profile.employee
            if not employee or serializer.validated_data["patient"].assigned_doctor_id!=employee.pk: raise PermissionDenied("Doctors can only record diagnoses for assigned patients.")
            serializer.save(doctor=employee)
        else: serializer.save()
    def perform_update(self,serializer):
        if role_of(self.request.user)=="Doctor":
            employee=self.request.user.profile.employee
            if not employee or serializer.validated_data.get("patient",serializer.instance.patient).assigned_doctor_id!=employee.pk: raise PermissionDenied("Doctors can only update diagnoses for assigned patients.")
            serializer.save(doctor=employee)
        else: serializer.save()

class TestViewSet(HospitalViewSet):
    queryset=Test.objects.select_related("patient","doctor").all(); serializer_class=TestSerializer
    search_fields=["name","patient__name","patient__patient_id","doctor__name","status"]; ordering_fields=["test_date","status"]
    def get_queryset(self):
        qs=super().get_queryset()
        if role_of(self.request.user)=="Doctor": qs=qs.filter(Q(doctor__user_profile__user=self.request.user)|Q(patient__assigned_doctor__user_profile__user=self.request.user))
        return qs
    def perform_create(self,serializer):
        if role_of(self.request.user)=="Doctor":
            employee=self.request.user.profile.employee
            if not employee or serializer.validated_data["patient"].assigned_doctor_id!=employee.pk: raise PermissionDenied("Doctors can only order tests for assigned patients.")
            serializer.save(doctor=employee)
        else: serializer.save()
    def perform_update(self,serializer):
        if role_of(self.request.user)=="Doctor":
            employee=self.request.user.profile.employee
            if not employee or serializer.validated_data.get("patient",serializer.instance.patient).assigned_doctor_id!=employee.pk: raise PermissionDenied("Doctors can only update tests for assigned patients.")
            serializer.save(doctor=employee)
        else: serializer.save()

class EquipmentViewSet(HospitalViewSet):
    queryset=SurgicalEquipment.objects.select_related("department").all(); serializer_class=EquipmentSerializer
    search_fields=["name","equipment_id","department__name","category"]; ordering_fields=["name","equipment_id"]

class PrescriptionViewSet(HospitalViewSet):
    queryset=Prescription.objects.select_related("patient","doctor","medical_store").all(); serializer_class=PrescriptionSerializer
    search_fields=["medicine","patient__name","patient__patient_id","doctor__name","status"]; ordering_fields=["prescribed_on","status"]
    def get_queryset(self):
        qs=super().get_queryset()
        if role_of(self.request.user)=="Doctor": qs=qs.filter(doctor__user_profile__user=self.request.user)
        return qs

class MedicalStoreViewSet(HospitalViewSet):
    queryset=MedicalStore.objects.all().order_by("name"); serializer_class=MedicalStoreSerializer
    search_fields=["name","location"]

class PersonViewSet(HospitalViewSet):
    queryset=Person.objects.all(); serializer_class=PersonSerializer; search_fields=["name","phone"]

class CaretakerViewSet(HospitalViewSet):
    queryset=Caretaker.objects.select_related("person","patient").all(); serializer_class=CaretakerSerializer
    search_fields=["person__name","patient__name","patient__patient_id","relationship"]

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    profile=getattr(request.user,"profile",None)
    return Response({"id":request.user.pk,"username":request.user.username,"name":request.user.get_full_name() or request.user.username,"role":role_of(request.user),"employee_id":profile.employee_id if profile and profile.employee_id else None})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def data_revision(request):
    revision = DataRevision.objects.filter(pk=1).values_list("revision", flat=True).first()
    return Response({"revision": revision or 0})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    today=timezone.localdate(); start=today-timedelta(days=6)
    patient_series=[]
    for i in range(7):
        day=start+timedelta(days=i)
        patient_series.append({"date":day.strftime("%b %d"),"patients":Patient.objects.filter(created_at__date=day).count()})
    return Response({"total_patients":Patient.objects.count(),"total_doctors":Employee.objects.filter(is_active=True,job_title__icontains="doctor").count(),
        "total_departments":Department.objects.count(),"tests_today":Test.objects.filter(test_date=today).count(),
        "pending_tests":Test.objects.filter(status=Test.Status.PENDING).count(),"available_equipment":SurgicalEquipment.objects.filter(available=True).count(),
        "patient_trend":patient_series,"patients_by_department":list(Department.objects.annotate(total=Count("patients")).values("name","total")),
        "tests_by_type":list(Test.objects.values("name").annotate(total=Count("id")).order_by("-total")[:8]),
        "doctors_by_department":list(Department.objects.annotate(total=Count("employees",filter=Q(employees__job_title__icontains="doctor"))).values("name","total")),
        "recent_patients":PatientSerializer(Patient.objects.select_related("department")[:5],many=True).data})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def query(request):
    text=request.data.get("query","")
    if not isinstance(text,str) or not text.strip(): return Response({"query":"","type":"error","message":"Enter a query to search hospital data.","results":[]},status=status.HTTP_400_BAD_REQUEST)
    if len(text)>300: return Response({"query":"","type":"error","message":"Queries must be 300 characters or fewer.","results":[]},status=status.HTTP_400_BAD_REQUEST)
    return Response(run_query(text,request.user))

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def global_search(request):
    term=request.query_params.get("q","").strip()
    if not term: return Response({"results":[]})
    results=[]
    patients=Patient.objects.all()
    if role_of(request.user)=="Doctor": patients=patients.filter(assigned_doctor__user_profile__user=request.user)
    results += [{"id":x.pk,"type":"Patient","title":x.name,"subtitle":x.patient_id,"url":f"/patients/{x.pk}"} for x in patients.filter(Q(name__icontains=term)|Q(patient_id__icontains=term))[:5]]
    results += [{"id":x.pk,"type":"Doctor" if "doctor" in x.job_title.lower() else "Employee","title":x.name,"subtitle":x.department.name if x.department else x.job_title,"url":"/doctors"} for x in Employee.objects.select_related("department").filter(Q(name__icontains=term)|Q(employee_id__icontains=term)|Q(department__name__icontains=term))[:5]]
    results += [{"id":x.pk,"type":"Department","title":x.name,"subtitle":x.location,"url":"/departments"} for x in Department.objects.filter(Q(name__icontains=term)|Q(location__icontains=term))[:5]]
    tests=Test.objects.select_related("patient")
    if role_of(request.user)=="Doctor": tests=tests.filter(patient__assigned_doctor__user_profile__user=request.user)
    results += [{"id":x.pk,"type":"Test","title":x.name,"subtitle":x.patient.name,"url":"/tests"} for x in tests.filter(Q(name__icontains=term)|Q(patient__name__icontains=term))[:5]]
    results += [{"id":x.pk,"type":"Equipment","title":x.name,"subtitle":x.department.name if x.department else x.equipment_id,"url":"/equipment"} for x in SurgicalEquipment.objects.select_related("department").filter(Q(name__icontains=term)|Q(equipment_id__icontains=term))[:5]]
    return Response({"results":results})
