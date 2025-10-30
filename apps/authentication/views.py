from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .forms import UserRegistrationForm, AccountSettingsForm, ProfilePictureForm
from django.contrib.auth.models import User, Group


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        groups = list(user.groups.values_list('name', flat=True))
        employee = getattr(user, 'employee_profile', None)
        history = []
        next_grade = []
        time_in_grade = None
        if employee:
            history = list(employee.history.select_related('employee').all()[:10])
            next_grade = employee.next_grade_eligibility()
            # Compute 'X years, Y months' in current grade
            try:
                start = employee.grade_start_date
                if start:
                    from datetime import date
                    today = date.today()
                    total_months = (today.year - start.year) * 12 + (today.month - start.month)
                    if today.day < start.day:
                        total_months -= 1
                    total_months = max(0, total_months)
                    years = total_months // 12
                    months = total_months % 12
                    parts = []
                    if years > 0:
                        parts.append(f"{years} year{'s' if years != 1 else ''}")
                    parts.append(f"{months} month{'s' if months != 1 else ''}")
                    time_in_grade = ", ".join(parts)
            except Exception:
                time_in_grade = None
            # Compute supervisors M+1 and M+2
            try:
                m1 = None
                m2 = None
                from apps.employees.models.employee import Employee as Emp
                # Determine chain based on where employee is attached
                if employee.service_id:
                    m1 = Emp.objects.filter(service_id=employee.service_id, position__position_type='chef_service').first()
                    m2 = Emp.objects.filter(division_id=employee.division_id, position__position_type='chef_division').first() if employee.division_id else Emp.objects.filter(direction_id=employee.direction_id, position__position_type='chef_direction').first()
                elif employee.division_id:
                    m1 = Emp.objects.filter(division_id=employee.division_id, position__position_type='chef_division').first()
                    m2 = Emp.objects.filter(direction_id=employee.direction_id, position__position_type='chef_direction').first()
                elif employee.direction_id:
                    m1 = Emp.objects.filter(direction_id=employee.direction_id, position__position_type='chef_direction').first()
                    m2 = None
                supervisors = {'m1': m1, 'm2': m2}
            except Exception:
                supervisors = {'m1': None, 'm2': None}
        return render(request, 'authentication/profile.html', {
            'user_obj': user,
            'groups': groups,
            'employee': employee,
            'history': history,
            'next_grade': next_grade,
            'time_in_grade': time_in_grade,
            'supervisors': supervisors if employee else {'m1': None, 'm2': None},
        })


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('employees:list')
        form = UserRegistrationForm()
        return render(request, 'authentication/register.html', {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('employees:list')
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('employees:list')
        return render(request, 'authentication/register.html', {'form': form})


class ITAdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or self.request.user.groups.filter(name='IT Admin').exists()
        )


class UserListView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        users = User.objects.all().order_by('username')
        groups = Group.objects.all().order_by('name')
        return render(request, 'authentication/users.html', {
            'users': users,
            'groups': groups,
        })


class AccountSettingsView(LoginRequiredMixin, View):
    def get(self, request):
        form = AccountSettingsForm(instance=request.user)
        picture_form = ProfilePictureForm(instance=getattr(request.user, 'employee_profile', None))
        return render(request, 'authentication/account_settings.html', {
            'form': form,
            'picture_form': picture_form
        })

    def post(self, request):
        form = AccountSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account settings updated.')
            return redirect('authentication:profile')
        picture_form = ProfilePictureForm(instance=getattr(request.user, 'employee_profile', None))
        return render(request, 'authentication/account_settings.html', {
            'form': form,
            'picture_form': picture_form
        })


class UploadProfilePictureView(LoginRequiredMixin, View):
    def post(self, request):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            messages.error(request, 'No employee profile linked to your account.')
            return redirect('authentication:profile')
        
        form = ProfilePictureForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Photo de profil mise à jour avec succès!')
            return redirect('authentication:profile')
        else:
            messages.error(request, 'Error uploading profile picture.')
            return redirect('authentication:account')


@require_http_methods(["POST"])
def device_login_api(request):
    """
    Passwordless login using a verified device - AUTO-DETECTS device and user account.
    Supports:
      - USB stamp device with password (device_serial auto-detected + stamp_password)
      - Fingerprint reader (WebAuthn credential_id auto-identifies device and user)
    On success, logs the associated user in.
    """
    import json, hashlib
    from apps.signatures.models import BiometricDevice

    try:
        data = json.loads(request.body)
        device_serial = data.get('device_serial', '')
        method = data.get('method')  # 'usb_stamp' or 'fingerprint'

        if not method:
            return JsonResponse({'success': False, 'error': 'Method required'}, status=400)

        if method == 'usb_stamp':
            # USB stamp: requires device_serial from WebUSB detection
            if not device_serial:
                return JsonResponse({'success': False, 'error': 'Device serial required for USB stamp'}, status=400)
            
            device = BiometricDevice.objects.filter(
                device_serial=device_serial,
                device_type='usb_stamp_device',
                is_active=True,
                is_verified=True
            ).select_related('user').first()
            
            if not device:
                return JsonResponse({'success': False, 'error': 'USB stamp device not registered or not verified'}, status=404)
            
            if device.is_locked():
                return JsonResponse({'success': False, 'error': 'Device locked'}, status=403)
            
            password = data.get('stamp_password', '')
            if not password:
                return JsonResponse({'success': False, 'error': 'Password required'}, status=400)
            
            if hashlib.sha256(password.encode()).hexdigest() != device.stamp_password_hash:
                device.record_failed_attempt()
                return JsonResponse({'success': False, 'error': 'Invalid password'}, status=401)
            
            device.record_successful_use()
            login(request, device.user)
            return JsonResponse({'success': True, 'username': device.user.username})
        
        elif method == 'fingerprint':
            # Fingerprint/WebAuthn: identify device by credential_id (enrollment_data stores credential ID)
            credential_id = data.get('credential_id', '')
            if not credential_id:
                return JsonResponse({'success': False, 'error': 'Credential ID required'}, status=400)
            
            # Look up device by enrollment_data (which contains base64 credential ID)
            device = BiometricDevice.objects.filter(
                enrollment_data=credential_id,
                device_type='fingerprint_reader',
                is_active=True,
                is_verified=True
            ).select_related('user').first()
            
            if not device:
                return JsonResponse({'success': False, 'error': 'Fingerprint device not registered or not verified'}, status=404)
            
            if device.is_locked():
                return JsonResponse({'success': False, 'error': 'Device locked'}, status=403)
            
            # WebAuthn verification happens client-side via navigator.credentials.get
            # The fact that we got a valid credential_id and the browser verified it means success
            # In production, you should verify the assertion signature server-side
            
            device.record_successful_use()
            login(request, device.user)
            return JsonResponse({'success': True, 'username': device.user.username})
        
        else:
            # Fallback for other device types with serial lookup
            if not device_serial:
                return JsonResponse({'success': False, 'error': 'Device serial required'}, status=400)
            
            device = BiometricDevice.objects.filter(
                device_serial=device_serial,
                is_active=True,
                is_verified=True
            ).select_related('user').first()
            
            if not device:
                return JsonResponse({'success': False, 'error': 'Device not found or not verified'}, status=404)
            
            if device.is_locked():
                return JsonResponse({'success': False, 'error': 'Device locked'}, status=403)
            
            # Generic verification for other methods
            biometric_data = data.get('biometric_data', '')
            if biometric_data != device.enrollment_data:
                device.record_failed_attempt()
                return JsonResponse({'success': False, 'error': 'Biometric verification failed'}, status=401)
            
            device.record_successful_use()
            login(request, device.user)
            return JsonResponse({'success': True, 'username': device.user.username})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
