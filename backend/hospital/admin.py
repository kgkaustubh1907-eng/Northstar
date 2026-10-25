from django.contrib import admin
from .models import *
for model in [Department,Employee,Patient,Person,Caretaker,Diagnosis,Test,MedicalStore,Prescription,SurgicalEquipment,UserProfile]:
    admin.site.register(model)
