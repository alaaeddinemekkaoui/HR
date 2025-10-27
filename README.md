# HR Management System - IAV Hassan II

Complete HR management system built with Django for Institut Agronomique et Vétérinaire Hassan II, featuring employee management, leave tracking, document generation, and organizational hierarchy with support for educational institutions (Départements & Filières).

## 🚀 Features

### Core Modules
- **Employee Management**: Complete employee lifecycle with organizational hierarchy
- **Leave Management**: Request, approve, and track employee leaves with balance management
- **Document Generation**: Dynamic document templates (Attestations, Decisions, Custom templates)
- **Role-Based Access Control**: IT Admin, HR Admin, Managers, and Normal Users
- **Employment History**: Track grade progressions, contracts, and career changes
- **Organizational Structure**: Directions → Divisions → Services → Départements → Filières

### Technology Stack
- **Backend**: Django 4.2+ with MySQL 8.0
- **Frontend**: Server-rendered templates with Bootstrap 5
- **Document Generation**: WeasyPrint for PDF generation
- **Database**: MySQL 8.0 with phpMyAdmin interface
- **Containerization**: Docker Compose for easy deployment
- **Caching/Queue**: Redis (for future async tasks)

## 📋 Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- MySQL 8.0 (handled by Docker)

## 🔧 Quick Start

### 1. Clone and Setup

```powershell
git clone <repository-url>
cd HR
```

### 2. Start Services with Docker

```powershell
# Build and start all services
docker compose up -d --build

# Wait for MySQL to initialize (first time only)
# Check logs: docker compose logs db
```

### 3. Run Migrations

```powershell
# Apply database migrations
docker compose exec web python manage.py migrate
```

### 4. Seed Initial Data

**Important: Run seed commands in this order:**

```powershell
# 1. Create organizational structure, grades, and positions
docker compose exec web python manage.py seed_iav_data

# 2. Create roles and permissions
docker compose exec web python manage.py seed_roles

# 3. Create leave types
docker compose exec web python manage.py seed_leave_types

# 4. Create admin user (IT Admin with full access)
docker compose exec web python manage.py seed_admin_user

# 5. (Optional) Create sample employees for testing
docker compose exec web python manage.py seed_sample_employees
```

### 5. Access the System

- **HR Application**: http://localhost:8000
- **phpMyAdmin**: http://localhost:8080
  - Username: `root`
  - Password: `iav@2025`

## 👤 Default Admin Credentials

After running `seed_admin_user`:

```
Username: admin
Password: admin123
Email: admin@iav.ac.ma
Role: IT Admin (Superuser)
```

## 📁 Project Structure

```
HR/
├── apps/
│   ├── employees/          # Employee management
│   │   ├── models/         # Employee, Direction, Division, Service, Departement, Filiere
│   │   ├── views/          # Employee CRUD, History, Organizational views
│   │   ├── forms/          # Employee forms, History forms
│   │   ├── controllers/    # Business logic
│   │   └── management/     # Seed commands
│   ├── leaves/             # Leave management
│   │   ├── models.py       # LeaveRequest, LeaveType, EmployeeLeaveBalance
│   │   ├── views.py        # Leave requests, approvals, balance management
│   │   └── utils.py        # Scope and approval logic
│   ├── documents/          # Document generation
│   │   ├── models.py       # DocumentTemplate
│   │   ├── views.py        # Static and dynamic document generation
│   │   └── templates/      # Document templates (Attestations, etc.)
│   ├── roles/              # Role and permission management
│   ├── authentication/     # Login system
│   └── notifications/      # User notifications
├── hr_project/             # Django project settings
├── templates/              # Global templates
│   ├── base.html          # Bootstrap 5 base template (French)
│   ├── employees/         # Employee templates
│   ├── leaves/            # Leave templates
│   └── documents/         # Document templates
├── static/                 # CSS, JS, images
├── docker-compose.yml      # Docker services configuration
├── Dockerfile             # Web service container
└── requirements.txt       # Python dependencies
```

## 🗄️ Database Schema

### Organizational Hierarchy

```
Direction (DG, SG, DE, DEAA)
    ├── Division
    │   ├── Service
    │   │   └── Departement
    │   │       └── Filiere
    │   └── Departement
    │       └── Filiere
    └── Service
        └── Departement
            └── Filiere
```

### Key Models
- **Employee**: Core employee data with organizational assignment
- **EmploymentHistory**: Track grade changes, contracts, retirement
- **LeaveRequest**: Leave applications with approval workflow
- **EmployeeLeaveBalance**: Annual leave balance tracking
- **DocumentTemplate**: Dynamic document generation templates
- **Position**: Job positions (Directeur, Chef Adjoint, Inspecteur, etc.)
- **Grade**: Moroccan public sector grades (Échelle 1-11, Hors Échelle)

## 👥 User Roles & Permissions

### IT Admin (Superuser)
- ✅ Full system access
- ✅ Manage all employees, leaves, documents
- ✅ Configure system settings
- ✅ Modify leave balances
- ✅ Access employment history
- ✅ Generate documents for any employee

### HR Admin
- ✅ View all employees and organizational structure
- ✅ View all leave requests (read-only)
- ✅ Generate documents for any employee
- ✅ Manage employee records
- ❌ Cannot approve/reject leaves (compliance)
- ❌ Cannot modify leave balances

### Managers (Chef Direction/Division/Service)
- ✅ View employees in their scope
- ✅ Approve/reject leave requests for direct reports
- ✅ View team leave calendar
- ❌ Cannot access other departments

### Normal User (Employee)
- ✅ View own profile and employment history
- ✅ Request leaves
- ✅ View own leave balance and history
- ✅ Generate own attestations
- ❌ Cannot access other employees' data

## 📄 Document Generation

### Static Documents
- **Attestation de Travail**: Work certificate
- **Attestation de Salaire**: Salary certificate (requires input)
- **Décision de Congé**: Leave decision letter

### Custom Templates
- Create custom document templates via admin interface
- Use Django template syntax with employee context
- Generate PDF documents with WeasyPrint
- IT/HR Admins can generate for any employee via search

### Admin Document Generator
Access via sidebar: **Documents → Générer Documents (Admin)**
1. Search employee by name, matricule, or PPR
2. Select document type from dropdown
3. Generate and download PDF

## 🔄 Employment History Tracking

Track complete employee career progression:
- **Grade Changes**: Promotions, échelle/échelon advancement
- **Contracts**: New contracts, renewals, titularisation
- **Retirement**: Retirement tracking with post-retirement contracts
- **Document References**: Link to official decision documents
- **Approval Workflow**: History entries can be approved/pending

Access: Employee Detail Page → Employment History section

## 💼 Leave Management

### Leave Request Flow
1. Employee submits leave request
2. System calculates balance
3. Manager receives notification
4. Manager approves/rejects
5. History is tracked
6. Decision document generated

### Balance Management (IT Admin Only)
- View/modify leave balances per employee
- Reset balances annually
- Adjust for special cases
- Track opening, accrued, used, and closing balances

### Leave Types
- **CA**: Congé Annuel (22 days/year)
- **CM**: Congé Maladie (15 days/year)  
- **CE**: Congé Exceptionnel (10 days/year)
- **CM_MAT**: Congé Maternité (14 weeks)
- **CM_PAT**: Congé Paternité (3 days)
- **CSS**: Congé Sans Solde
- **CF**: Congé de Formation (12 days/year)

## 🏢 Organizational Structure Examples

### DEAA (Direction des Exploitations et de l'Appui à l'Agriculture)
- **Département Agronomie**
  - Filière Industries Alimentaires et Agricoles (IAA)
  - Filière Production Agricole (PA)
- **Département Horticulture**
  - Filière Horticulture
  - Filière Architecture du Paysage
- **Département Économie Rurale**
  - Filière Économie Agricole

### Direction des Études
- **Département Informatique**
  - Filière Génie Logiciel (GL)
  - Filière Intelligence Artificielle (IA)

## 🛠️ Development Commands

### Django Management Commands

```powershell
# Create migrations
docker compose exec web python manage.py makemigrations

# Apply migrations
docker compose exec web python manage.py migrate

# Create superuser manually
docker compose exec web python manage.py createsuperuser

# Access Django shell
docker compose exec web python manage.py shell

# Collect static files
docker compose exec web python manage.py collectstatic
```

### Database Management

```powershell
# Access MySQL shell
docker compose exec db mysql -u root -p
# Password: iav@2025

# Backup database
docker compose exec db mysqldump -u root -piav@2025 hr_db > backup.sql

# Restore database
docker compose exec -T db mysql -u root -piav@2025 hr_db < backup.sql
```

### Docker Commands

```powershell
# View logs
docker compose logs -f web

# Restart services
docker compose restart

# Stop all services
docker compose down

# Remove volumes (caution: deletes data)
docker compose down -v
```

## 🌐 Localization

The system is fully localized in French:
- ✅ All templates translated
- ✅ Form labels and help text
- ✅ Success/error messages
- ✅ Email notifications
- ✅ Document templates

## 📦 Seed Data Summary

After running all seed commands:
- **4 Directions**: DG, SG, DE, DEAA
- **Multiple Divisions and Services**
- **4 Départements** with **7 Filières**
- **28 Grades** (Moroccan public sector classification)
- **13 Positions** (including Directeur, Inspecteur, Chef Département/Filière)
- **7 Leave Types**
- **3 System Roles** with function permissions
- **1 Admin User** (IT Admin)
- Sample employees (if seed_sample_employees is run)

## 🔐 Security Notes

- Change default passwords in production
- Update `SECRET_KEY` in production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Configure CORS properly if adding frontend
- Regularly backup database

## 📝 Contributing

1. Follow Django coding standards
2. Maintain French localization
3. Document new features
4. Test role-based access control
5. Update seed data for new models

## 📞 Support

For issues or questions related to IAV Hassan II deployment:
- Contact IT Department
- Review Django documentation: https://docs.djangoproject.com/
- Check Docker Compose documentation: https://docs.docker.com/compose/

## 📜 License

Internal use - Institut Agronomique et Vétérinaire Hassan II

