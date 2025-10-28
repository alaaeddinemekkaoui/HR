from django.db import models, transaction
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import JSONField


class Direction(models.Model):
    """Top-level organizational unit (e.g., Direction des Études, Direction Générale)"""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),  # Filtered dropdown queries
        ]
        verbose_name = 'Direction'
        verbose_name_plural = 'Directions'

    def __str__(self):
        return self.name


class Division(models.Model):
    """Division within a Direction"""
    direction = models.ForeignKey(Direction, on_delete=models.PROTECT, related_name='divisions')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['direction', 'name']
        unique_together = [['direction', 'code']]
        indexes = [
            models.Index(fields=['direction', 'is_active']),  # Cascading dropdown queries
        ]
        verbose_name = 'Division'
        verbose_name_plural = 'Divisions'

    def __str__(self):
        return f"{self.direction.code} - {self.name}"


class Service(models.Model):
    """Service can be attached either to a Division or directly to a Direction"""
    direction = models.ForeignKey(Direction, on_delete=models.PROTECT, related_name='services', null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='services', null=True, blank=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = [['division', 'code'], ['direction', 'code']]
        indexes = [
            models.Index(fields=['division', 'is_active']),   # Cascading dropdown by division
            models.Index(fields=['direction', 'is_active']),  # Cascading dropdown by direction
        ]
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    def __str__(self):
        if self.division:
            return f"{self.division.direction.code}/{self.division.code} - {self.name}"
        if self.direction:
            return f"{self.direction.code} - {self.name}"
        return self.name

    def clean(self):
        super().clean()
        # Exactly one of direction or division must be set
        if bool(self.direction) == bool(self.division):
            raise ValidationError('A service must be linked to either a direction or a division (but not both).')


class Departement(models.Model):
    """Département - Academic department (can belong to Direction, Division, or Service)"""
    direction = models.ForeignKey(Direction, on_delete=models.PROTECT, related_name='departements', null=True, blank=True)
    division = models.ForeignKey('Division', on_delete=models.PROTECT, related_name='departements', null=True, blank=True)
    service = models.ForeignKey('Service', on_delete=models.PROTECT, related_name='departements', null=True, blank=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # At least one organizational unit must be set
        if not any([self.direction, self.division, self.service]):
            raise ValidationError("Département doit appartenir à au moins une Direction, Division ou Service")

    def __str__(self):
        if self.service:
            return f"{self.service.code} - {self.name}"
        elif self.division:
            return f"{self.division.code} - {self.name}"
        elif self.direction:
            return f"{self.direction.code} - {self.name}"
        return self.name


class Filiere(models.Model):
    """Filière (program/track) within a Département"""
    departement = models.ForeignKey(Departement, on_delete=models.PROTECT, related_name='filieres')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['departement', 'name']
        unique_together = [['departement', 'code']]
        verbose_name = 'Filière'
        verbose_name_plural = 'Filières'

    def __str__(self):
        return f"{self.departement.name} - {self.name}"


class Grade(models.Model):
    """Public sector grade (e.g., Ingénieur, Ingénieur Principal, Technicien)"""
    CATEGORY_CHOICES = [
        ('cadre_superieur', 'Cadre Supérieur'),
        ('cadre', 'Cadre'),
        ('maitrise', 'Maîtrise'),
        ('execution', 'Exécution'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Grade'
        verbose_name_plural = 'Grades'

    def __str__(self):
        return self.name


class Position(models.Model):
    """Position/Function (e.g., Chef de Service, Chef de Division, Ingénieur, Secrétaire)"""
    POSITION_TYPE_CHOICES = [
        ('directeur', 'Directeur'),
        ('chef_direction', 'Chef de Direction'),
        ('chef_adjoint', 'Chef Adjoint'),
        ('chef_division', 'Chef de Division'),
        ('chef_service', 'Chef de Service'),
        ('chef_departement', 'Chef de Département'),
        ('chef_filiere', 'Chef de Filière'),
        ('inspecteur', 'Inspecteur'),
        ('employee', 'Employé'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    position_type = models.CharField(max_length=20, choices=POSITION_TYPE_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position_type', 'name']
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'

    def __str__(self):
        return self.name


class Employee(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('on_leave', 'En Congé'),
        ('detached', 'Détaché'),
        ('suspended', 'Suspendu'),
        ('retired', 'Retraité'),
        ('inactive', 'Inactif'),
    ]
    
    CONTRACT_TYPE_CHOICES = [
        ('titulaire', 'Titulaire'),
        ('contractuel', 'Contractuel'),
        ('stagiaire', 'Stagiaire'),
        ('detache', 'Détaché'),
    ]
    
    # Personal Information
    first_name = models.CharField(max_length=100, verbose_name='Prénom')
    last_name = models.CharField(max_length=100, verbose_name='Nom')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, verbose_name='Photo de profil')
    cin = models.CharField(max_length=20, unique=True, verbose_name='CIN')
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[RegexValidator(r'^\+?212[0-9]{9}$|^0[0-9]{9}$', 'Format: 0612345678 ou +212612345678')],
        verbose_name='Téléphone'
    )
    date_of_birth = models.DateField(verbose_name='Date de naissance')
    address = models.TextField(blank=True, verbose_name='Adresse')
    
    # Administrative Information
    employee_id = models.CharField(max_length=20, unique=True, db_index=True, verbose_name='Matricule')
    ppr = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='PPR')
    retirement_age = models.PositiveIntegerField(default=63, verbose_name='Âge de retraite')
    
    # Organizational Structure (IAV Hassan II hierarchy)
    direction = models.ForeignKey(Direction, on_delete=models.PROTECT, related_name='employees', verbose_name='Direction')
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='employees', null=True, blank=True, verbose_name='Division')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='employees', null=True, blank=True, verbose_name='Service')
    departement = models.ForeignKey('Departement', on_delete=models.PROTECT, related_name='employees', null=True, blank=True, verbose_name='Département')
    filiere = models.ForeignKey('Filiere', on_delete=models.PROTECT, related_name='employees', null=True, blank=True, verbose_name='Filière')
    
    # Position and Grade (Moroccan public sector)
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='employees', verbose_name='Fonction')
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name='employees', verbose_name='Grade')
    
    # Échelle (Scale: 1-11, then Hors Échelle) - Based on Moroccan public sector classification
    echelle = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        null=True,
        blank=True,
        verbose_name='Échelle',
        help_text='Échelle de 1 à 11'
    )
    hors_echelle = models.BooleanField(default=False, verbose_name='Hors Échelle')
    echelon = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
        verbose_name='Échelon',
        help_text='Échelon de 1 à 10'
    )
    
    # Employment Information
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, default='titulaire', verbose_name='Type de contrat')
    hire_date = models.DateField(verbose_name='Date de recrutement')
    contract_start_date = models.DateField(null=True, blank=True, verbose_name='Date début contrat')
    contract_end_date = models.DateField(null=True, blank=True, verbose_name='Date fin contrat')
    titularisation_date = models.DateField(null=True, blank=True, verbose_name='Date de titularisation')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Statut')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Auth link
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Organizational filtering (most common queries)
            models.Index(fields=['direction', 'status']),
            models.Index(fields=['division', 'status']),
            models.Index(fields=['service', 'status']),
            # Search and sorting
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['employee_id']),  # Exact ID lookups
            # Grade and progression queries
            models.Index(fields=['grade', 'echelle']),
            models.Index(fields=['position']),
            # Composite index for filtered lists
            models.Index(fields=['direction', 'division', 'service']),
            # Date-based queries
            models.Index(fields=['-created_at']),  # Recent employees first
            models.Index(fields=['hire_date']),    # Seniority queries
        ]
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def organizational_path(self):
        """Full organizational path"""
        parts = [self.direction.name]
        if self.division:
            parts.append(self.division.name)
        if self.service:
            parts.append(self.service.name)
        return " → ".join(parts)
    
    @property
    def grade_display(self):
        """Display grade with échelle/hors échelle"""
        if self.hors_echelle:
            return f"{self.grade.name} - Hors Échelle"
        elif self.echelle:
            echelon_part = f" - Échelon {self.echelon}" if self.echelon else ""
            return f"{self.grade.name} - Échelle {self.echelle}{echelon_part}"
        return self.grade.name

    # --- Derived info and progression helpers ---
    @property
    def is_titularised(self) -> bool:
        return bool(self.titularisation_date and self.titularisation_date <= timezone.now().date())

    @property
    def retirement_date(self):
        dob = self.date_of_birth
        if not dob:
            return None
        try:
            return dob.replace(year=dob.year + int(self.retirement_age))
        except ValueError:
            # Handle Feb 29 -> Feb 28 in non-leap retirement year
            return dob.replace(month=2, day=28, year=dob.year + int(self.retirement_age))

    @property
    def grade_start_date(self):
        last = self.history.filter(change_type='grade').order_by('-effective_date', '-created_at').first()  # type: ignore[attr-defined]
        if last:
            return last.effective_date
        # Default to titularisation date if present, else hire date
        return self.titularisation_date or self.hire_date

    @property
    def years_in_grade(self) -> int:
        start = self.grade_start_date
        if not start:
            return 0
        today = timezone.now().date()
        years = today.year - start.year - ((today.month, today.day) < (start.month, start.day))
        return max(0, years)
    
    @property
    def time_in_grade_display(self) -> str:
        """Return formatted string showing time in grade (years or months)"""
        start = self.grade_start_date
        if not start:
            return "0 months"
        
        today = timezone.now().date()
        years = today.year - start.year - ((today.month, today.day) < (start.month, start.day))
        
        if years >= 1:
            return f"{years} year{'s' if years > 1 else ''}"
        else:
            # Calculate months
            months = (today.year - start.year) * 12 + today.month - start.month
            if today.day < start.day:
                months -= 1
            months = max(0, months)
            return f"{months} month{'s' if months != 1 else ''}"

        @property
        def estimated_titularisation_date(self):
            """Calculate estimated titularisation date (hire_date + 1 year)"""
            if not self.hire_date:
                return None
            from datetime import timedelta
            return self.hire_date + timedelta(days=365)
    
        @property
        def is_eligible_for_titularisation(self):
            """Check if employee has completed 1 year since hire date"""
            if self.titularisation_date:  # Already titularised
                return False
            if self.contract_type == 'permanent':  # Already permanent
                return False
            if not self.hire_date:
                return False
        
            today = timezone.now().date()
            one_year_after_hire = self.estimated_titularisation_date
            return today >= one_year_after_hire

    def next_grade_eligibility(self):
        """Return a list of dicts describing possible next grades with dates, based on configured rules."""
        rules = GradeProgressionRule.objects.filter(source_grade=self.grade, is_active=True).select_related('target_grade')
        base_date = self.grade_start_date
        results = []
        for r in rules:
            with_exam_date = None
            without_exam_date = None
            if base_date and r.years_with_exam is not None:
                try:
                    with_exam_date = base_date.replace(year=base_date.year + r.years_with_exam)
                except ValueError:
                    with_exam_date = base_date.replace(month=2, day=28, year=base_date.year + r.years_with_exam)
            if base_date and r.years_without_exam is not None:
                try:
                    without_exam_date = base_date.replace(year=base_date.year + r.years_without_exam)
                except ValueError:
                    without_exam_date = base_date.replace(month=2, day=28, year=base_date.year + r.years_without_exam)
            results.append({
                'target_grade': r.target_grade,
                'with_exam_years': r.years_with_exam,
                'without_exam_years': r.years_without_exam,
                'with_exam_date': with_exam_date,
                'without_exam_date': without_exam_date,
                'description': r.description,
            })
        return results

    def save(self, *args, **kwargs):
        # Auto-increment employee_id if empty
        if not self.employee_id:
            with transaction.atomic():
                last = Employee.objects.order_by('-created_at').first()
                next_id = 1000
                if last and last.employee_id:
                    try:
                        next_id = int(str(last.employee_id)) + 1
                    except Exception:
                        next_id = 1000
                self.employee_id = str(next_id)

        # History logging for important changes
        tracked = ['grade', 'position', 'direction', 'division', 'service', 'status', 'contract_type', 'echelle', 'echelon', 'hors_echelle']
        changes = {}
        if self.pk:
            old = Employee.objects.get(pk=self.pk)
            for f in tracked:
                old_val = getattr(old, f)
                new_val = getattr(self, f)
                # For FKs, store display string or id
                if isinstance(old_val, models.Model):
                    old_val = getattr(old_val, 'id', None)
                if isinstance(new_val, models.Model):
                    new_val = getattr(new_val, 'id', None)
                if old_val != new_val:
                    changes[f] = {'from': old_val, 'to': new_val}

        super().save(*args, **kwargs)

        if changes:
            change_type = 'other'
            if any(k in changes for k in ['grade', 'echelle', 'echelon', 'hors_echelle']):
                change_type = 'grade'
            elif 'position' in changes:
                change_type = 'position'
            elif any(k in changes for k in ['direction', 'division', 'service']):
                change_type = 'organization'
            elif any(k in changes for k in ['status', 'contract_type']):
                change_type = 'status'
            EmploymentHistory.objects.create(
                employee=self,
                change_type=change_type,
                changes=changes,
                effective_date=timezone.now().date(),
                note='Auto-logged change'
            )


class EmploymentHistory(models.Model):
    """Track employment changes: grade progression, contracts, retirement, etc."""
    
    CHANGE_TYPES = [
        ('grade', 'Changement de Grade'),
        ('echelle', 'Changement d\'Échelle'),
        ('echelon', 'Changement d\'Échelon'),
        ('contract', 'Nouveau Contrat'),
        ('contract_renewal', 'Renouvellement de Contrat'),
        ('titularisation', 'Titularisation'),
        ('retirement', 'Retraite'),
        ('contract_end', 'Fin de Contrat'),
        ('status', 'Changement de Statut'),
        ('position', 'Changement de Poste'),
        ('organization', 'Changement Organisationnel'),
        ('other', 'Autre'),
    ]
    
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='history')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES, verbose_name='Type de changement')
    
    # Store detailed changes as JSON for flexibility
    changes = JSONField(default=dict, verbose_name='Détails des changements')
    
    # Contract specific fields
    contract_start_date = models.DateField(null=True, blank=True, verbose_name='Date début contrat')
    contract_end_date = models.DateField(null=True, blank=True, verbose_name='Date fin contrat')
    
    # Retirement specific
    retirement_date = models.DateField(null=True, blank=True, verbose_name='Date de retraite')
    post_retirement_contract = models.BooleanField(default=False, verbose_name='Contrat post-retraite')
    
    effective_date = models.DateField(verbose_name='Date effective')
    note = models.TextField(blank=True, verbose_name='Notes')
    document_reference = models.CharField(max_length=200, blank=True, verbose_name='Référence document')
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_employment_changes',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date', '-created_at']
        verbose_name = 'Historique d\'emploi'
        verbose_name_plural = 'Historiques d\'emploi'

    def __str__(self):
        return f"{self.employee} - {self.get_change_type_display()} @ {self.effective_date}"

    @property
    def change_summary(self):
        """Generate a human-readable summary"""
        if self.change_type == 'contract' and self.contract_start_date:
            return f"Contrat: {self.contract_start_date} → {self.contract_end_date or 'Indéterminé'}"
        elif self.change_type == 'retirement' and self.retirement_date:
            status = " (avec contrat post-retraite)" if self.post_retirement_contract else ""
            return f"Retraite: {self.retirement_date}{status}"
        elif self.changes:
            # Format JSON changes
            parts = []
            for key, value in self.changes.items():
                if isinstance(value, dict) and 'from' in value and 'to' in value:
                    parts.append(f"{key}: {value['from']} → {value['to']}")
            return ", ".join(parts) if parts else self.get_change_type_display()
        return self.get_change_type_display()


class GradeProgressionRule(models.Model):
    """Defines progression from one grade to another with time requirements (with/without exam)."""
    source_grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='progression_from')
    target_grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='progression_to')
    years_with_exam = models.PositiveIntegerField(null=True, blank=True)
    years_without_exam = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('source_grade', 'target_grade')]
        ordering = ['source_grade__name', 'target_grade__name']

    def __str__(self):
        return f"{self.source_grade} → {self.target_grade}"

    def clean(self):
        super().clean()
        # Enforce that progression is within the same grade category (e.g., Ingénieur family only)
        if self.source_grade_id and self.target_grade_id:
            if self.source_grade.category != self.target_grade.category:
                from django.core.exceptions import ValidationError
                raise ValidationError('Progression must remain within the same grade category (e.g., Ingénieur → Ingénieur).')
