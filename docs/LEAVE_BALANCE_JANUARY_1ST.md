# Leave Balance Management - January 1st Process

## Overview
The leave balance system automatically initializes new year balances for all employees on January 1st. This document explains the process and how to set it up.

## What Happens on January 1st

### Automatic Process:
1. **Carry Over**: Unused leave days from the previous year are carried forward
2. **Expiration**: Old balances (older than `carry_over_years`) are marked as expired
3. **New Accrual**: Fresh allocation of annual leave days for the new year (22 days for Congé Annuel)
4. **Reset Used**: "Used" days counter starts at 0 for the new year

### Example:
```
Employee: Ahmed El Mansouri
Previous Year (2025): 22 days allocated, 5 days used, 17 days remaining

January 1st, 2026:
- Opening: 17 days (carried over from 2025)
- Accrued: 22 days (new allocation for 2026)
- Used: 0 days
- Closing: 39 days (17 + 22 - 0)
```

## Manual Command (Run on January 1st)

### Initialize Balances for Current Year:
```bash
docker compose exec web python manage.py initialize_year_balances
```

### Initialize for Specific Year:
```bash
docker compose exec web python manage.py initialize_year_balances --year 2026
```

### Force Update (if balances already exist):
```bash
docker compose exec web python manage.py initialize_year_balances --force
```

## Automated Scheduling Options

### Option 1: Cron Job (Linux/Docker)
Add to your server's crontab:
```bash
# Run at midnight on January 1st every year
0 0 1 1 * cd /path/to/HR && docker compose exec web python manage.py initialize_year_balances
```

### Option 2: Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task → Name: "Leave Balance New Year"
3. Trigger: Yearly, January 1st, 00:00
4. Action: Start a program
5. Program: `powershell.exe`
6. Arguments: 
   ```
   -Command "cd C:\Users\user\Desktop\HR; docker compose exec web python manage.py initialize_year_balances"
   ```

### Option 3: Django-Crontab (Python Package)
Install: `pip install django-crontab`

Add to `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'django_crontab',
]

CRONJOBS = [
    # Run at midnight on January 1st
    ('0 0 1 1 *', 'django.core.management.call_command', ['initialize_year_balances']),
]
```

Then run: `python manage.py crontab add`

### Option 4: Celery Beat (Recommended for Production)
Install: `pip install celery django-celery-beat`

Create task in `apps/leaves/tasks.py`:
```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def initialize_year_balances():
    call_command('initialize_year_balances')
```

Schedule in Celery Beat:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'initialize-year-balances': {
        'task': 'apps.leaves.tasks.initialize_year_balances',
        'schedule': crontab(hour=0, minute=0, day_of_month=1, month_of_year=1),
    },
}
```

## Verification After Running

### Check Balances Were Created:
```bash
docker compose exec web python manage.py shell -c "
from apps.leaves.models import EmployeeLeaveBalance
from django.utils import timezone
year = timezone.now().year
count = EmployeeLeaveBalance.objects.filter(year=year).count()
print(f'Balances for {year}: {count}')
"
```

### View Sample Balance:
```bash
docker compose exec web python manage.py shell -c "
from apps.leaves.models import EmployeeLeaveBalance
balance = EmployeeLeaveBalance.objects.filter(year=2026).first()
if balance:
    print(f'{balance.employee.full_name} - {balance.leave_type.name}')
    print(f'Opening: {balance.opening}')
    print(f'Accrued: {balance.accrued}')
    print(f'Closing: {balance.closing}')
"
```

## Carry-Over Rules

### Default Settings (per Leave Type):
- **Congé Annuel**: 2 years carry-over (configurable in admin)
- **Other leave types**: Check `carry_over_years` field in leave type settings

### Expiration Example:
```
Year 2023: 10 days unused
Year 2024: Still available (1 year old)
Year 2025: Still available (2 years old)
Year 2026: EXPIRED (3 years old, exceeds carry_over_years=2)
```

## Monthly Accrual During the Year

### Prorata Calculation:
- Employees hired mid-year get prorated leave
- Formula: (annual_days / 12) × months_worked
- Example: Hired in July = 6 months × 1.83 days/month = 11 days

### Update Accruals Monthly:
```bash
docker compose exec web python manage.py recalculate_leave_balances
```

## Related Commands

### Recalculate All Balances:
```bash
python manage.py recalculate_leave_balances
```

### Rollover from Specific Year:
```bash
python manage.py rollover_leave_balances --from-year 2025 --to-year 2026
```

### Create Initial Balances (First Time Setup):
```bash
python manage.py seed_leave_balances --year 2025
```

## Troubleshooting

### Problem: Balances Already Exist
**Solution**: Use `--force` flag
```bash
python manage.py initialize_year_balances --force
```

### Problem: Wrong Accrual Amounts
**Solution**: Check leave type settings
1. Go to Admin → Leaves → Leave Types
2. Verify `annual_days` field (should be 22 for Congé Annuel)
3. Check `prorata_monthly` setting
4. Run recalculate command

### Problem: Days Not Carried Over
**Solution**: Check previous year balances exist
```bash
docker compose exec web python manage.py shell -c "
from apps.leaves.models import EmployeeLeaveBalance
prev_year = 2025
count = EmployeeLeaveBalance.objects.filter(year=prev_year).count()
print(f'Previous year balances: {count}')
"
```

## Best Practices

1. **Run Before Business Hours**: Schedule for 00:01 on January 1st
2. **Test First**: Run with `--year 2027` to test without affecting current data
3. **Backup Database**: Always backup before running
4. **Verify Results**: Check a few employee balances manually
5. **Notify HR**: Send email confirmation after successful run
6. **Log Output**: Redirect command output to a log file

### Example with Logging:
```bash
docker compose exec web python manage.py initialize_year_balances 2>&1 | tee /var/log/leave_balances_$(date +%Y).log
```

## Summary

✅ **Automatic**: Set up once, runs every January 1st
✅ **Carry-Over**: Preserves unused days (up to carry_over_years limit)
✅ **Expiration**: Automatically expires old balances
✅ **Prorata**: Handles mid-year hires correctly
✅ **Audit Trail**: Logs all operations

For support or questions, contact the IT Admin or System Administrator.
