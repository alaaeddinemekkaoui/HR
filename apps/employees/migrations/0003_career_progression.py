# Generated migration for career progression models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0002_service_direction_division_nullable_employee_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='retirement_age',
            field=models.PositiveIntegerField(default=63, verbose_name='Âge de retraite'),
        ),
        migrations.CreateModel(
            name='EmploymentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_type', models.CharField(choices=[('grade', 'Grade/Scale change'), ('position', 'Position change'), ('organization', 'Organization change'), ('status', 'Status/Contract change'), ('other', 'Other')], max_length=20)),
                ('changes', models.JSONField(default=dict)),
                ('effective_date', models.DateField()),
                ('note', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='employees.employee')),
            ],
            options={'ordering': ['-effective_date', '-created_at']},
        ),
        migrations.CreateModel(
            name='GradeProgressionRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('years_with_exam', models.PositiveIntegerField(blank=True, null=True)),
                ('years_without_exam', models.PositiveIntegerField(blank=True, null=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('source_grade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progression_from', to='employees.grade')),
                ('target_grade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progression_to', to='employees.grade')),
            ],
            options={'ordering': ['source_grade__name', 'target_grade__name']},
        ),
        migrations.AlterUniqueTogether(
            name='gradeprogressionrule',
            unique_together={('source_grade', 'target_grade')},
        ),
    ]
