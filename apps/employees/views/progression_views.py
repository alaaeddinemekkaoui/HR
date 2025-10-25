from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models.employee import GradeProgressionRule
from ..forms.progression_forms import GradeProgressionRuleForm


class RuleListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'employees.view_gradeprogressionrule'
    def get(self, request):
        rules = GradeProgressionRule.objects.select_related('source_grade', 'target_grade').order_by('source_grade__name', 'target_grade__name')
        return render(request, 'employees/progression/rules_list.html', {'rules': rules})


class RuleCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'employees.add_gradeprogressionrule'
    def get(self, request):
        form = GradeProgressionRuleForm()
        return render(request, 'employees/progression/rule_form.html', {'form': form, 'mode': 'create'})
    def post(self, request):
        form = GradeProgressionRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rule created.')
            return redirect('employees:rules_list')
        return render(request, 'employees/progression/rule_form.html', {'form': form, 'mode': 'create'})


class RuleEditView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'employees.change_gradeprogressionrule'
    def get(self, request, pk):
        rule = get_object_or_404(GradeProgressionRule, pk=pk)
        form = GradeProgressionRuleForm(instance=rule)
        return render(request, 'employees/progression/rule_form.html', {'form': form, 'mode': 'edit', 'rule': rule})
    def post(self, request, pk):
        rule = get_object_or_404(GradeProgressionRule, pk=pk)
        form = GradeProgressionRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rule updated.')
            return redirect('employees:rules_list')
        return render(request, 'employees/progression/rule_form.html', {'form': form, 'mode': 'edit', 'rule': rule})


class RuleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'employees.delete_gradeprogressionrule'
    def post(self, request, pk):
        rule = get_object_or_404(GradeProgressionRule, pk=pk)
        rule.delete()
        messages.success(request, 'Rule deleted.')
        return redirect('employees:rules_list')
    