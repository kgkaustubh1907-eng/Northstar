from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
router=DefaultRouter()
router.register("patients",views.PatientViewSet)
router.register("employees",views.EmployeeViewSet)
router.register("departments",views.DepartmentViewSet)
router.register("diagnoses",views.DiagnosisViewSet)
router.register("tests",views.TestViewSet)
router.register("equipment",views.EquipmentViewSet)
router.register("prescriptions",views.PrescriptionViewSet)
router.register("medical-stores",views.MedicalStoreViewSet)
router.register("people",views.PersonViewSet)
router.register("caretakers",views.CaretakerViewSet)
urlpatterns=[path("",include(router.urls)),path("dashboard/",views.dashboard),path("query/",views.query),path("search/",views.global_search),path("auth/me/",views.current_user)]
