"""
Async views for high-performance operations under load
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from django.db.models import Q

from ..models import Employee, Direction, Division, Service
from ..async_cache import (
    get_cached_value_async,
    aget_cache,
    aset_cache,
    CacheKeys,
    CacheTTL,
)


class AsyncGetDivisionsAPIView(View):
    """Async API view for divisions by direction - non-blocking under load"""
    
    async def get(self, request):
        direction_id = request.GET.get('direction_id')
        if not direction_id:
            return JsonResponse({'divisions': []})
        
        cache_key = CacheKeys.DIVISIONS_BY_DIRECTION.format(id=direction_id)
        
        # Non-blocking cache get
        divisions = await aget_cache(cache_key)
        
        if divisions is None:
            # Non-blocking database query
            @sync_to_async
            def fetch_divisions():
                return list(
                    Division.objects.filter(
                        direction_id=direction_id, is_active=True
                    ).values('id', 'name')
                )
            
            divisions = await fetch_divisions()
            
            # Non-blocking cache set
            await aset_cache(cache_key, divisions, CacheTTL.LONG)
        
        return JsonResponse({'divisions': divisions})


class AsyncGetServicesAPIView(View):
    """Async API view for services by direction/division - non-blocking under load"""
    
    async def get(self, request):
        direction_id = request.GET.get('direction_id')
        division_id = request.GET.get('division_id')
        
        if division_id:
            cache_key = CacheKeys.SERVICES_BY_DIVISION.format(id=division_id)
            
            services = await aget_cache(cache_key)
            
            if services is None:
                @sync_to_async
                def fetch_services():
                    return list(
                        Service.objects.filter(
                            division_id=division_id, is_active=True
                        ).values('id', 'name')
                    )
                
                services = await fetch_services()
                await aset_cache(cache_key, services, CacheTTL.LONG)
            
            return JsonResponse({'services': services})
            
        elif direction_id:
            cache_key = CacheKeys.SERVICES_BY_DIRECTION.format(id=direction_id)
            
            services = await aget_cache(cache_key)
            
            if services is None:
                @sync_to_async
                def fetch_services():
                    return list(
                        Service.objects.filter(
                            direction_id=direction_id,
                            division__isnull=True,
                            is_active=True
                        ).values('id', 'name')
                    )
                
                services = await fetch_services()
                await aset_cache(cache_key, services, CacheTTL.LONG)
            
            return JsonResponse({'services': services})
        
        return JsonResponse({'services': []})


class AsyncEmployeeListView(LoginRequiredMixin, View):
    """
    Async employee list view for optimal performance under load.
    
    Uses async cache operations and database queries to prevent blocking.
    Supports all the same filtering, search, and pagination as sync view.
    """
    
    async def get(self, request):
        # Fetch base employee list asynchronously
        @sync_to_async
        def get_base_employees():
            return Employee.objects.select_related(
                'direction', 'division', 'service', 'departement', 
                'filiere', 'grade', 'position', 'user'
            ).prefetch_related('user__groups').all()
        
        employees = await get_base_employees()
        
        # Apply scope restrictions (async-safe)
        @sync_to_async
        def apply_scope(queryset):
            user = request.user
            
            if user.is_superuser or user.groups.filter(name='IT Admin').exists():
                return queryset
            
            emp = getattr(user, 'employee_profile', None)
            is_hr_admin = user.groups.filter(name='HR Admin').exists()
            
            if is_hr_admin:
                return queryset
            
            # Regular users: restrict to same direction
            scope_q = Q()
            if emp and emp.direction_id:
                scope_q = Q(direction_id=emp.direction_id)
            else:
                if emp:
                    scope_q = Q(user_id=user.id)
                else:
                    scope_q = Q(pk__in=[])
            
            return queryset.filter(scope_q)
        
        employees = await apply_scope(employees)
        
        # Search functionality (async-safe)
        search_query = (request.GET.get('search') or request.GET.get('q') or '').strip()
        if search_query:
            @sync_to_async
            def apply_search(queryset, query):
                terms = [t for t in query.split() if t]
                base_q = Q()
                initialized = False
                
                for term in terms:
                    term_q = (
                        Q(first_name__icontains=term) |
                        Q(last_name__icontains=term) |
                        Q(email__icontains=term) |
                        Q(employee_id__icontains=term) |
                        Q(ppr__icontains=term) |
                        Q(cin__icontains=term) |
                        Q(phone__icontains=term) |
                        Q(position__name__icontains=term) |
                        Q(grade__name__icontains=term) |
                        Q(direction__name__icontains=term) |
                        Q(division__name__icontains=term) |
                        Q(service__name__icontains=term)
                    )
                    base_q = term_q if not initialized else (base_q & term_q)
                    initialized = True
                
                if query.isdigit():
                    base_q = base_q | Q(employee_id=query) | Q(ppr=query)
                
                return queryset.filter(base_q)
            
            employees = await apply_search(employees, search_query)
        
        # Apply filters (async-safe)
        status_filter = request.GET.get('status', '')
        direction_id = request.GET.get('direction')
        division_id = request.GET.get('division')
        service_id = request.GET.get('service')
        
        @sync_to_async
        def apply_filters(queryset):
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if direction_id:
                queryset = queryset.filter(direction_id=direction_id)
            if division_id:
                queryset = queryset.filter(division_id=division_id)
            if service_id:
                queryset = queryset.filter(service_id=service_id)
            return queryset
        
        employees = await apply_filters(employees)
        
        # Pagination (async-safe)
        page_size = request.GET.get('page_size', '10')
        try:
            page_size = int(page_size)
            if page_size not in [5, 10, 25, 50, 100]:
                page_size = 10
        except (ValueError, TypeError):
            page_size = 10
        
        @sync_to_async
        def paginate(queryset, size, page_num):
            paginator = Paginator(queryset, size)
            return paginator.get_page(page_num)
        
        page_number = request.GET.get('page', 1)
        page_obj = await paginate(employees, page_size, page_number)
        
        # Get dropdown choices (cached, async)
        @sync_to_async
        def get_dropdowns():
            user = request.user
            
            if user.is_superuser or user.groups.filter(name__in=['HR Admin', 'IT Admin']).exists():
                directions = Direction.objects.filter(is_active=True).order_by('name')
                divisions = Division.objects.filter(is_active=True).order_by('name')
                services = Service.objects.filter(is_active=True).order_by('name')
            elif user.is_authenticated:
                emp = getattr(user, 'employee_profile', None)
                if emp and emp.service_id:
                    directions = Direction.objects.filter(pk=emp.direction_id, is_active=True)
                    divisions = Division.objects.filter(pk=emp.division_id, is_active=True)
                    services = Service.objects.filter(pk=emp.service_id, is_active=True)
                elif emp and emp.division_id:
                    directions = Direction.objects.filter(pk=emp.direction_id, is_active=True)
                    divisions = Division.objects.filter(pk=emp.division_id, is_active=True)
                    services = Service.objects.filter(division_id=emp.division_id, is_active=True)
                elif emp and emp.direction_id:
                    directions = Direction.objects.filter(pk=emp.direction_id, is_active=True)
                    divisions = Division.objects.filter(direction_id=emp.direction_id, is_active=True)
                    services = Service.objects.filter(direction_id=emp.direction_id, is_active=True)
                else:
                    directions = Direction.objects.none()
                    divisions = Division.objects.none()
                    services = Service.objects.none()
            else:
                directions = Direction.objects.none()
                divisions = Division.objects.none()
                services = Service.objects.none()
            
            return list(directions), list(divisions), list(services)
        
        directions, divisions, services = await get_dropdowns()
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'direction_id': int(direction_id) if direction_id else None,
            'division_id': int(division_id) if division_id else None,
            'service_id': int(service_id) if service_id else None,
            'directions': directions,
            'divisions': divisions,
            'services': services,
            'status_choices': Employee.STATUS_CHOICES,
        }
        
        return render(request, 'employees/list.html', context)
