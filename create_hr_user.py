import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_portal.settings')
django.setup()

from accounts.models import CustomUser

# Create HR user
if not CustomUser.objects.filter(username='hr_admin').exists():
    hr_user = CustomUser.objects.create_user(
        username='hr_admin',
        email='hr@company.com',
        password='Hr@123456',
        role='HR',
        first_name='HR',
        last_name='Admin'
    )
    print('✓ HR user created successfully!')
    print(f'  Username: hr_admin')
    print(f'  Password: Hr@123456')
    print(f'  Email: hr@company.com')
    print(f'  Role: HR')
else:
    print('✓ HR user already exists')
    print(f'  Username: hr_admin')
    print(f'  Password: Hr@123456')
