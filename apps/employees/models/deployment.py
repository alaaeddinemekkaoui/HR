"""
Deployment (Déplacement) Models
- DeploymentForfaitaire: Fixed monthly allowance (no approval needed)
- OrdreMission: Travel authorization request (requires approval)
- DeploymentReal: Actual expenses tracking (HR/Admin only, no approval)
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class GradeDeploymentRate(models.Model):
    """
    Default deployment rates per grade
    Tracks historical changes to rates
    """
    grade = models.ForeignKey('employees.Grade', on_delete=models.CASCADE, related_name='deployment_rates')
    daily_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Taux journalier'
    )
    monthly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Taux mensuel forfaitaire'
    )
    effective_date = models.DateField(
        verbose_name='Date d\'effet',
        help_text='Date à partir de laquelle ce taux est applicable'
    )
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rates')
    notes = models.TextField(blank=True, verbose_name='Notes')
    
    class Meta:
        verbose_name = 'Taux de déplacement par grade'
        verbose_name_plural = 'Taux de déplacement par grade'
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['grade', 'is_active']),
            models.Index(fields=['effective_date']),
        ]
    
    def __str__(self):
        return f"{self.grade.name} - {self.monthly_rate} DH/mois (dès {self.effective_date})"
    
    @classmethod
    def get_current_rate(cls, grade):
        """Get the currently active rate for a grade"""
        from django.utils import timezone
        return cls.objects.filter(
            grade=grade,
            is_active=True,
            effective_date__lte=timezone.now().date()
        ).first()


class DeploymentForfaitaire(models.Model):
    """
    Fixed monthly deployment allowance
    Employee requests standard monthly allowance - NO APPROVAL needed
    Generates document to be signed by hierarchy
    """
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='deployments_forfaitaire',
        verbose_name='Employé'
    )
    month = models.DateField(
        verbose_name='Mois',
        help_text='Premier jour du mois concerné'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Montant (DH)'
    )
    default_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Montant par défaut'
    )
    
    # Request details
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deployment_forfaitaire_requests',
        verbose_name='Créé par'
    )
    
    notes = models.TextField(blank=True, verbose_name='Notes')
    document_reference = models.CharField(max_length=255, blank=True, verbose_name='Référence document')
    
    # Signature tracking
    is_signed = models.BooleanField(default=False, verbose_name='Signé par la hiérarchie')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deployment_forfaitaire_signatures',
        verbose_name='Signé par'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Déplacement forfaitaire'
        verbose_name_plural = 'Déplacements forfaitaires'
        ordering = ['-month', '-requested_at']
        unique_together = ['employee', 'month']
        indexes = [
            models.Index(fields=['employee', 'month']),
            models.Index(fields=['requested_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.month.strftime('%B %Y')} - {self.amount} DH"


class OrdreMission(models.Model):
    """
    Mission Order - Employee requests travel authorization
    Requires hierarchy approval before travel
    Generates signed document upon approval
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ]
    
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='ordres_mission',
        verbose_name='Employé'
    )
    
    # Travel details
    start_date = models.DateField(verbose_name='Date de départ')
    end_date = models.DateField(verbose_name='Date de retour')
    location = models.CharField(max_length=255, verbose_name='Lieu de mission')
    purpose = models.TextField(verbose_name='Objet de la mission')
    
    # Supporting document (optional)
    ordre_document = models.FileField(
        upload_to='ordres_mission/',
        null=True,
        blank=True,
        verbose_name='Document ordre de mission (preuve)'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Statut'
    )
    
    # Request details
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name='Demandé le')
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordre_mission_requests',
        verbose_name='Demandé par'
    )
    
    # Approval details
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Examiné le')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordre_mission_reviews',
        verbose_name='Examiné par'
    )
    review_notes = models.TextField(blank=True, verbose_name='Notes d\'examen')
    
    notes = models.TextField(blank=True, verbose_name='Notes')
    
    # Signature tracking (after approval)
    is_signed = models.BooleanField(default=False, verbose_name='Signé par la hiérarchie')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordre_mission_signatures',
        verbose_name='Signé par'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ordre de mission'
        verbose_name_plural = 'Ordres de mission'
        ordering = ['-start_date', '-requested_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status', 'requested_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.location} ({self.start_date} → {self.end_date})"
    
    def calculate_days(self):
        """Calculate number of days between start and end date"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None
    
    def can_edit(self):
        """Check if this ordre can still be edited"""
        return self.status == 'pending'
    
    def can_approve(self):
        """Check if this ordre can be approved"""
        return self.status == 'pending'


class DeploymentReal(models.Model):
    """
    Actual deployment expenses with receipts
    ONLY for HR/Admin users to track actual expenses
    Does NOT require approval - administrative tracking only
    Generates document to be signed
    """
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='deployments_real',
        verbose_name='Employé'
    )
    
    # Travel details
    start_date = models.DateField(verbose_name='Date de départ')
    end_date = models.DateField(verbose_name='Date de retour')
    location = models.CharField(max_length=255, verbose_name='Lieu de mission')
    purpose = models.TextField(verbose_name='Objet de la mission')
    
    # Financial details
    daily_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Taux journalier (DH)',
        help_text='Laisser vide si montant total direct'
    )
    number_of_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='Nombre de jours'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Montant total (DH)'
    )
    default_daily_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Taux journalier par défaut'
    )
    
    # Created by (HR/Admin only)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deployment_real_created',
        verbose_name='Créé par'
    )
    
    notes = models.TextField(blank=True, verbose_name='Notes')
    document_reference = models.CharField(max_length=255, blank=True, verbose_name='Référence document')
    
    # Signature tracking
    is_signed = models.BooleanField(default=False, verbose_name='Signé par la hiérarchie')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de signature')
    signed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deployment_real_signatures',
        verbose_name='Signé par'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Déplacement réel'
        verbose_name_plural = 'Déplacements réels'
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['employee']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.location} ({self.start_date} → {self.end_date}) - {self.total_amount} DH"
    
    def calculate_days(self):
        """Calculate number of days between start and end date"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None
    
    def save(self, *args, **kwargs):
        # Auto-calculate number of days if not provided
        if not self.number_of_days and self.start_date and self.end_date:
            self.number_of_days = self.calculate_days()
        
        # Auto-calculate total if daily rate is provided
        if self.daily_rate and self.number_of_days and not self.total_amount:
            self.total_amount = self.daily_rate * self.number_of_days
        
        super().save(*args, **kwargs)
