from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .employee import Employee, Grade


class EmploymentHistory(models.Model):
    """Track employment changes: grade progression, contracts, retirement, etc."""
    
    CHANGE_TYPE_CHOICES = [
        ('grade', 'Changement de Grade'),
        ('echelle', 'Changement d\'Échelle'),
        ('echelon', 'Changement d\'Échelon'),
        ('contract', 'Nouveau Contrat'),
        ('contract_renewal', 'Renouvellement de Contrat'),
        ('titularisation', 'Titularisation'),
        ('retirement', 'Retraite'),
        ('contract_end', 'Fin de Contrat'),
        ('status_change', 'Changement de Statut'),
        ('position_change', 'Changement de Poste'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='employment_history'
    )
    change_type = models.CharField(
        max_length=20, 
        choices=CHANGE_TYPE_CHOICES,
        verbose_name='Type de changement'
    )
    change_date = models.DateField(
        verbose_name='Date du changement'
    )
    
    # Grade/Échelle/Échelon tracking
    previous_grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_previous_grade',
        verbose_name='Grade précédent'
    )
    new_grade = models.ForeignKey(
        Grade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='history_new_grade',
        verbose_name='Nouveau grade'
    )
    previous_echelle = models.IntegerField(null=True, blank=True, verbose_name='Échelle précédente')
    new_echelle = models.IntegerField(null=True, blank=True, verbose_name='Nouvelle échelle')
    previous_echelon = models.IntegerField(null=True, blank=True, verbose_name='Échelon précédent')
    new_echelon = models.IntegerField(null=True, blank=True, verbose_name='Nouvel échelon')
    
    # Contract tracking
    contract_start_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Date début contrat'
    )
    contract_end_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Date fin contrat'
    )
    contract_type = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Type de contrat'
    )
    
    # Retirement tracking
    retirement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date de retraite'
    )
    post_retirement_contract = models.BooleanField(
        default=False,
        verbose_name='Contrat post-retraite'
    )
    
    # Status tracking
    previous_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Statut précédent'
    )
    new_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Nouveau statut'
    )
    
    # Position tracking
    previous_position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Poste précédent'
    )
    new_position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nouveau poste'
    )
    
    # Documentation and approval
    notes = models.TextField(
        blank=True,
        verbose_name='Notes'
    )
    document_reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Référence document'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_employment_changes',
        verbose_name='Approuvé par'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_employment_changes',
        verbose_name='Créé par'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-change_date', '-created_at']
        verbose_name = 'Historique d\'emploi'
        verbose_name_plural = 'Historiques d\'emploi'
        indexes = [
            models.Index(fields=['employee', 'change_type']),
            models.Index(fields=['change_date']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_change_type_display()} - {self.change_date}"

    @property
    def change_summary(self):
        """Generate a human-readable summary of the change"""
        if self.change_type == 'grade':
            return f"Grade: {self.previous_grade} → {self.new_grade}"
        elif self.change_type == 'echelle':
            return f"Échelle: {self.previous_echelle} → {self.new_echelle}"
        elif self.change_type == 'echelon':
            return f"Échelon: {self.previous_echelon} → {self.new_echelon}"
        elif self.change_type in ['contract', 'contract_renewal']:
            return f"Contrat: {self.contract_start_date} → {self.contract_end_date}"
        elif self.change_type == 'titularisation':
            return f"Titularisation: {self.change_date}"
        elif self.change_type == 'retirement':
            return f"Retraite: {self.retirement_date}"
        elif self.change_type == 'status_change':
            return f"Statut: {self.previous_status} → {self.new_status}"
        elif self.change_type == 'position_change':
            return f"Poste: {self.previous_position} → {self.new_position}"
        return self.get_change_type_display()
