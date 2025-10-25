from django.contrib import admin
from .models import Direction, Division, Service, Grade, Position, Employee


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'direction', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'direction__name')
    list_filter = ('direction', 'is_active')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'division', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'division__name')
    list_filter = ('division__direction', 'division', 'is_active')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('category', 'is_active')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'position_type', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('position_type', 'is_active')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'full_name', 'cin', 'direction', 'division', 'service', 'position', 'grade', 'contract_type', 'status')
    search_fields = ('first_name', 'last_name', 'employee_id', 'cin', 'email', 'ppr')
    list_filter = ('status', 'contract_type', 'direction', 'division', 'grade', 'hors_echelle')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informations Personnelles', {
            'fields': ('first_name', 'last_name', 'cin', 'date_of_birth', 'email', 'phone', 'address')
        }),
        ('Informations Administratives', {
            'fields': ('employee_id', 'ppr')
        }),
        ('Structure Organisationnelle', {
            'fields': ('direction', 'division', 'service')
        }),
        ('Fonction et Grade', {
            'fields': ('position', 'grade', 'echelle', 'hors_echelle', 'echelon')
        }),
        ('Informations d\'Emploi', {
            'fields': ('contract_type', 'hire_date', 'contract_start_date', 'contract_end_date', 'titularisation_date', 'status')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
