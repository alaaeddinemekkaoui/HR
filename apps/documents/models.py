from django.db import models
from django.contrib.auth.models import User


class DocumentTemplate(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    content = models.TextField(help_text="Django template content. Use variables like {{ employee.full_name }}, {{ employee.cin }}, {{ today }}.")
    hr_only = models.BooleanField(default=True, help_text="If checked, only HR/Admin can render this template.")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doc_templates_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doc_templates_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name
