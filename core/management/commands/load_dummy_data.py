"""
Management command to load dummy data for Khael Solutions.
Run with: python manage.py load_dummy_data
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    User, Department, DepartmentMember,
    Job, JobUpdate, Resource, ResourceUsage,
    ResourceHistory, Purchase, PurchaseResource, Alert,
)


class Command(BaseCommand):
    help = 'Load dummy data for development and testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n  Loading dummy data...\n')
        self.create_users()
        self.create_departments()
        self.assign_members()
        self.create_resources()
        self.create_purchases()
        self.create_jobs()
        self.create_resource_usage()
        self.create_alerts()
        self.stdout.write(self.style.SUCCESS('\n  Dummy data loaded successfully!\n'))
        self.stdout.write('   Superuser login  -> username: admin      password: admin123')
        self.stdout.write('   Manager login    -> username: manager1   password: pass123')
        self.stdout.write('   Staff logins     -> username: staff1-6   password: pass123\n')

    def create_users(self):
        self.stdout.write('  Creating users...')
        self.admin = User.objects.create_superuser(
            username='admin', password='admin123',
            first_name='Kwame', last_name='Mensah',
            email='admin@khaelsolutions.com', role='super_admin',
        )
        self.manager1 = User.objects.create_user(
            username='manager1', password='pass123',
            first_name='Abena', last_name='Asante',
            email='abena@khaelsolutions.com', role='manager',
        )
        self.manager2 = User.objects.create_user(
            username='manager2', password='pass123',
            first_name='Kofi', last_name='Boateng',
            email='kofi@khaelsolutions.com', role='manager',
        )
        self.staff1 = User.objects.create_user(username='staff1', password='pass123', first_name='Ama',    last_name='Owusu',    email='ama@khaelsolutions.com',    role='staff')
        self.staff2 = User.objects.create_user(username='staff2', password='pass123', first_name='Yaw',    last_name='Darko',    email='yaw@khaelsolutions.com',    role='staff')
        self.staff3 = User.objects.create_user(username='staff3', password='pass123', first_name='Akosua', last_name='Frimpong', email='akosua@khaelsolutions.com', role='staff')
        self.staff4 = User.objects.create_user(username='staff4', password='pass123', first_name='Kojo',   last_name='Amponsah', email='kojo@khaelsolutions.com',   role='staff')
        self.staff5 = User.objects.create_user(username='staff5', password='pass123', first_name='Efua',   last_name='Mensah',   email='efua@khaelsolutions.com',   role='staff')
        self.staff6 = User.objects.create_user(username='staff6', password='pass123', first_name='Nana',   last_name='Agyei',    email='nana@khaelsolutions.com',   role='staff')

    def create_departments(self):
        self.stdout.write('  Creating departments...')
        self.dept_printing   = Department.objects.create(name='Printing Services',    description='Handles all print jobs including banners, flyers, business cards, and large-format printing.', hod=self.manager1)
        self.dept_network    = Department.objects.create(name='Network & IT',         description='Responsible for network setup, configuration, maintenance, and IT support for clients.',       hod=self.manager2)
        self.dept_multimedia = Department.objects.create(name='Multimedia Production', description='Covers photography, videography, graphic design, and digital content creation.',               hod=self.manager1)

    def assign_members(self):
        self.stdout.write('  Assigning staff to departments...')
        DepartmentMember.objects.create(user=self.staff1, department=self.dept_printing)
        DepartmentMember.objects.create(user=self.staff2, department=self.dept_printing)
        DepartmentMember.objects.create(user=self.staff3, department=self.dept_network)
        DepartmentMember.objects.create(user=self.staff4, department=self.dept_network)
        DepartmentMember.objects.create(user=self.staff5, department=self.dept_multimedia)
        DepartmentMember.objects.create(user=self.staff6, department=self.dept_multimedia)

    def create_resources(self):
        self.stdout.write('  Creating resources...')
        self.paper_a4      = Resource.objects.create(title='A4 Paper (80gsm)',          unit='reams',  quantity=Decimal('45'),  unit_cost=Decimal('32.00'),  reorder_level=Decimal('10'))
        self.paper_a3      = Resource.objects.create(title='A3 Paper (80gsm)',          unit='reams',  quantity=Decimal('18'),  unit_cost=Decimal('58.00'),  reorder_level=Decimal('5'))
        self.ink_black     = Resource.objects.create(title='Black Ink Cartridge',       unit='units',  quantity=Decimal('8'),   unit_cost=Decimal('120.00'), reorder_level=Decimal('5'))
        self.ink_colour    = Resource.objects.create(title='Colour Ink Cartridge',      unit='units',  quantity=Decimal('4'),   unit_cost=Decimal('185.00'), reorder_level=Decimal('5'))
        self.vinyl         = Resource.objects.create(title='Vinyl Banner Roll',         unit='metres', quantity=Decimal('60'),  unit_cost=Decimal('22.50'),  reorder_level=Decimal('10'))
        self.laminate      = Resource.objects.create(title='Lamination Film (A4)',      unit='rolls',  quantity=Decimal('3'),   unit_cost=Decimal('75.00'),  reorder_level=Decimal('4'))
        self.network_cable = Resource.objects.create(title='CAT6 Network Cable',        unit='metres', quantity=Decimal('200'), unit_cost=Decimal('4.50'),   reorder_level=Decimal('50'))
        self.rj45          = Resource.objects.create(title='RJ45 Connectors',           unit='units',  quantity=Decimal('150'), unit_cost=Decimal('0.80'),   reorder_level=Decimal('50'))
        self.switch        = Resource.objects.create(title='8-Port Network Switch',     unit='units',  quantity=Decimal('3'),   unit_cost=Decimal('320.00'), reorder_level=Decimal('2'))
        self.sd_card       = Resource.objects.create(title='SD Card (64GB)',            unit='units',  quantity=Decimal('6'),   unit_cost=Decimal('55.00'),  reorder_level=Decimal('3'))
        self.backdrop      = Resource.objects.create(title='Photography Backdrop',      unit='units',  quantity=Decimal('2'),   unit_cost=Decimal('180.00'), reorder_level=Decimal('1'))
        self.usb_drive     = Resource.objects.create(title='USB Flash Drive (32GB)',    unit='units',  quantity=Decimal('12'),  unit_cost=Decimal('25.00'),  reorder_level=Decimal('5'))

    def create_purchases(self):
        self.stdout.write('  Creating purchases...')
        p1 = Purchase.objects.create(created_by=self.manager1, notes='Monthly paper and ink stock replenishment.', purchase_total=Decimal('0'))
        items1 = [(self.paper_a4, Decimal('30'), Decimal('30.00')), (self.paper_a3, Decimal('10'), Decimal('55.00')), (self.ink_black, Decimal('5'), Decimal('115.00')), (self.ink_colour, Decimal('4'), Decimal('180.00'))]
        total1 = Decimal('0')
        for r, q, c in items1:
            PurchaseResource.objects.create(purchase=p1, resource=r, quantity=q, unit_cost=c)
            total1 += q * c
        p1.purchase_total = total1; p1.save()

        p2 = Purchase.objects.create(created_by=self.manager2, notes='Network equipment restock for campus installations.', purchase_total=Decimal('0'))
        items2 = [(self.network_cable, Decimal('100'), Decimal('4.20')), (self.rj45, Decimal('100'), Decimal('0.75')), (self.switch, Decimal('2'), Decimal('310.00'))]
        total2 = Decimal('0')
        for r, q, c in items2:
            if r.unit_cost != c:
                ResourceHistory.objects.create(resource=r, purchase=p2, old_price=r.unit_cost, new_price=c)
                r.unit_cost = c; r.save()
            PurchaseResource.objects.create(purchase=p2, resource=r, quantity=q, unit_cost=c)
            total2 += q * c
        p2.purchase_total = total2; p2.save()

        p3 = Purchase.objects.create(created_by=self.manager1, notes='Multimedia department supplies.', purchase_total=Decimal('0'))
        items3 = [(self.sd_card, Decimal('5'), Decimal('55.00')), (self.usb_drive, Decimal('10'), Decimal('24.00')), (self.backdrop, Decimal('1'), Decimal('175.00'))]
        total3 = Decimal('0')
        for r, q, c in items3:
            PurchaseResource.objects.create(purchase=p3, resource=r, quantity=q, unit_cost=c)
            total3 += q * c
        p3.purchase_total = total3; p3.save()

    def create_jobs(self):
        self.stdout.write('  Creating jobs...')
        today = timezone.now().date()

        self.job1  = Job.objects.create(title='Business Cards — GoldLink Ventures',      department=self.dept_printing,   service_type='printing',   assigned_to=self.staff1, created_by=self.manager1, client_name='GoldLink Ventures Ltd',      client_contact='0244123456', status='completed',   priority='high',   price=Decimal('350.00'),  start_date=today-timedelta(14), due_date=today-timedelta(10), completed_at=timezone.now()-timedelta(11), description='500 double-sided business cards for GoldLink Ventures. Glossy finish, full colour.')
        self.job2  = Job.objects.create(title='Event Banner — UPSA Graduation 2025',     department=self.dept_printing,   service_type='printing',   assigned_to=self.staff2, created_by=self.staff1,   client_name='UPSA Events Committee',      client_contact='0302123789', status='in_progress', priority='urgent', price=Decimal('800.00'),  start_date=today-timedelta(3),  due_date=today+timedelta(2),  description='4 large-format vinyl banners (3m x 2m) for UPSA 2025 graduation ceremony.')
        self.job3  = Job.objects.create(title='Flyer Printing — Accra Food Festival',    department=self.dept_printing,   service_type='printing',   assigned_to=self.staff1, created_by=self.manager1, client_name='Accra Food Festival Org.',   client_contact='0201987654', status='pending',     priority='medium', price=Decimal('420.00'),  start_date=today,               due_date=today+timedelta(5),  description='1000 A5 full-colour flyers. Double-sided printing.')
        self.job4  = Job.objects.create(title='Laminated ID Cards — Tema Port Authority',department=self.dept_printing,   service_type='printing',   assigned_to=self.staff2, created_by=self.manager1, client_name='Tema Port Authority',        client_contact='0303456789', status='on_hold',     priority='low',    price=Decimal('560.00'),  start_date=today-timedelta(7),  due_date=today-timedelta(2),  description='200 laminated staff ID cards. Client yet to supply full staff list and photos.')
        self.job5  = Job.objects.create(title='Brochure Design & Print — KBH Hospital',  department=self.dept_printing,   service_type='printing',   assigned_to=self.staff1, created_by=self.staff2,   client_name='KBH Private Hospital',       client_contact='0244765432', status='cancelled',   priority='medium', price=Decimal('670.00'),  start_date=today-timedelta(20), due_date=today-timedelta(15), description='Tri-fold brochures for hospital services. Cancelled — client changed vendor.')
        self.job6  = Job.objects.create(title='LAN Setup — Kumasi Polytechnic Lab',      department=self.dept_network,    service_type='network_it', assigned_to=self.staff3, created_by=self.manager2, client_name='Kumasi Technical University', client_contact='0322098765', status='completed',   priority='high',   price=Decimal('2200.00'), start_date=today-timedelta(21), due_date=today-timedelta(14), completed_at=timezone.now()-timedelta(15), description='Full LAN installation for 30-node computer lab.')
        self.job7  = Job.objects.create(title='WiFi Configuration — Devtraco Estate',    department=self.dept_network,    service_type='network_it', assigned_to=self.staff4, created_by=self.staff3,   client_name='Devtraco Properties',        client_contact='0302876543', status='in_progress', priority='high',   price=Decimal('1500.00'), start_date=today-timedelta(4),  due_date=today+timedelta(3),  description='WiFi access point installation for 3-block residential estate.')
        self.job8  = Job.objects.create(title='Network Audit — Stanbic Bank Branch',     department=self.dept_network,    service_type='network_it', assigned_to=self.staff3, created_by=self.manager2, client_name='Stanbic Bank Ghana',         client_contact='0302611000', status='pending',     priority='urgent', price=Decimal('3500.00'), start_date=today+timedelta(1),  due_date=today+timedelta(6),  description='Comprehensive network security audit for Osu branch.')
        self.job9  = Job.objects.create(title='CCTV Network Integration — Melcom Store', department=self.dept_network,    service_type='network_it', assigned_to=self.staff4, created_by=self.manager2, client_name='Melcom Ghana Ltd',           client_contact='0302789012', status='pending',     priority='medium', price=Decimal('1800.00'), start_date=today-timedelta(1),  due_date=today-timedelta(1),  description='Connect 16 CCTV cameras to central NVR system. Spintex Road branch.')
        self.job10 = Job.objects.create(title='Corporate Photography — Ecobank Ghana',   department=self.dept_multimedia, service_type='multimedia', assigned_to=self.staff5, created_by=self.manager1, client_name='Ecobank Ghana',              client_contact='0302681000', status='completed',   priority='high',   price=Decimal('1200.00'), start_date=today-timedelta(10), due_date=today-timedelta(7),  completed_at=timezone.now()-timedelta(8), description='Executive headshots and team photography for 25 staff members.')
        self.job11 = Job.objects.create(title='Product Video — Kasapreko Company',       department=self.dept_multimedia, service_type='multimedia', assigned_to=self.staff6, created_by=self.staff5,   client_name='Kasapreko Company Ltd',      client_contact='0244334455', status='in_progress', priority='high',   price=Decimal('2500.00'), start_date=today-timedelta(5),  due_date=today+timedelta(4),  description='60-second promotional product video. Includes post-production editing.')
        self.job12 = Job.objects.create(title='Graphic Design — MTN Ghana Campaign',     department=self.dept_multimedia, service_type='multimedia', assigned_to=self.staff5, created_by=self.manager1, client_name='MTN Ghana',                  client_contact='0244300000', status='pending',     priority='urgent', price=Decimal('1800.00'), start_date=today,               due_date=today+timedelta(3),  description='Digital billboard and social media assets for Q2 campaign. 12 design variants.')

        self.stdout.write('  Creating job timeline updates...')
        JobUpdate.objects.create(job=self.job1,  updated_by=self.manager1, status='pending',     comment='Job created and assigned to Ama.')
        JobUpdate.objects.create(job=self.job1,  updated_by=self.staff1,   status='in_progress', comment='Design approved by client. Printing started.')
        JobUpdate.objects.create(job=self.job1,  updated_by=self.staff1,   status='completed',   comment='500 cards printed and delivered to client.')
        JobUpdate.objects.create(job=self.job2,  updated_by=self.staff1,   status='pending',     comment='Job registered. Awaiting design files from client.')
        JobUpdate.objects.create(job=self.job2,  updated_by=self.staff2,   status='in_progress', comment='Design files received. Printing 2 of 4 banners complete.')
        JobUpdate.objects.create(job=self.job4,  updated_by=self.manager1, status='pending',     comment='Job created.')
        JobUpdate.objects.create(job=self.job4,  updated_by=self.staff2,   status='on_hold',     comment='Client has not supplied staff photos. Job on hold pending client response.')
        JobUpdate.objects.create(job=self.job5,  updated_by=self.manager1, status='pending',     comment='Job created.')
        JobUpdate.objects.create(job=self.job5,  updated_by=self.manager1, status='cancelled',   comment='Client cancelled — switched to another vendor.')
        JobUpdate.objects.create(job=self.job6,  updated_by=self.manager2, status='pending',     comment='Job created and team assigned.')
        JobUpdate.objects.create(job=self.job6,  updated_by=self.staff3,   status='in_progress', comment='Cabling complete. Switch configuration in progress.')
        JobUpdate.objects.create(job=self.job6,  updated_by=self.staff3,   status='completed',   comment='All 30 nodes connected and tested. Client signed off.')
        JobUpdate.objects.create(job=self.job9,  updated_by=self.manager2, status='pending',     comment='Job registered. Due date already passed — client delayed approval.')
        JobUpdate.objects.create(job=self.job10, updated_by=self.manager1, status='pending',     comment='Job created.')
        JobUpdate.objects.create(job=self.job10, updated_by=self.staff5,   status='in_progress', comment='On-location shoot complete. Studio session scheduled.')
        JobUpdate.objects.create(job=self.job10, updated_by=self.staff5,   status='completed',   comment='All photos edited and delivered via Google Drive link.')
        JobUpdate.objects.create(job=self.job11, updated_by=self.staff5,   status='pending',     comment='Job registered.')
        JobUpdate.objects.create(job=self.job11, updated_by=self.staff6,   status='in_progress', comment='Filming complete. Post-production editing underway.')

    def create_resource_usage(self):
        self.stdout.write('  Recording resource usage...')
        ResourceUsage.objects.create(job=self.job1,  resource=self.paper_a4,      quantity=Decimal('2'),  unit_cost=Decimal('30.00'),  recorded_by=self.staff1)
        ResourceUsage.objects.create(job=self.job1,  resource=self.ink_colour,    quantity=Decimal('1'),  unit_cost=Decimal('180.00'), recorded_by=self.staff1)
        ResourceUsage.objects.create(job=self.job2,  resource=self.vinyl,         quantity=Decimal('24'), unit_cost=Decimal('22.50'),  recorded_by=self.staff2)
        ResourceUsage.objects.create(job=self.job2,  resource=self.ink_colour,    quantity=Decimal('2'),  unit_cost=Decimal('185.00'), recorded_by=self.staff2)
        ResourceUsage.objects.create(job=self.job6,  resource=self.network_cable, quantity=Decimal('85'), unit_cost=Decimal('4.20'),   recorded_by=self.staff3)
        ResourceUsage.objects.create(job=self.job6,  resource=self.rj45,          quantity=Decimal('80'), unit_cost=Decimal('0.75'),   recorded_by=self.staff3)
        ResourceUsage.objects.create(job=self.job6,  resource=self.switch,        quantity=Decimal('2'),  unit_cost=Decimal('310.00'), recorded_by=self.staff3)
        ResourceUsage.objects.create(job=self.job7,  resource=self.network_cable, quantity=Decimal('30'), unit_cost=Decimal('4.50'),   recorded_by=self.staff4)
        ResourceUsage.objects.create(job=self.job7,  resource=self.rj45,          quantity=Decimal('25'), unit_cost=Decimal('0.80'),   recorded_by=self.staff4)
        ResourceUsage.objects.create(job=self.job10, resource=self.sd_card,       quantity=Decimal('2'),  unit_cost=Decimal('55.00'),  recorded_by=self.staff5)
        ResourceUsage.objects.create(job=self.job10, resource=self.usb_drive,     quantity=Decimal('1'),  unit_cost=Decimal('24.00'),  recorded_by=self.staff5)
        ResourceUsage.objects.create(job=self.job11, resource=self.sd_card,       quantity=Decimal('2'),  unit_cost=Decimal('55.00'),  recorded_by=self.staff6)
        ResourceUsage.objects.create(job=self.job11, resource=self.backdrop,      quantity=Decimal('1'),  unit_cost=Decimal('175.00'), recorded_by=self.staff6)
        ResourceUsage.objects.create(job=self.job11, resource=self.usb_drive,     quantity=Decimal('2'),  unit_cost=Decimal('25.00'),  recorded_by=self.staff6)

    def create_alerts(self):
        self.stdout.write('  Creating alerts...')
        Alert.objects.create(job=self.job9,  alert_type='overdue_job',      severity='critical', message='Job "CCTV Network Integration — Melcom Store" (#9) is overdue.', resolved=False)
        Alert.objects.create(job=self.job4,  alert_type='overdue_job',      severity='warning',  message='Job "Laminated ID Cards — Tema Port Authority" (#4) is on hold and past its due date.', resolved=False)
        Alert.objects.create(resource=self.laminate,   alert_type='low_stock', severity='warning', message='Resource "Lamination Film (A4)" is low: 3 rolls remaining (reorder: 4).', resolved=False)
        Alert.objects.create(resource=self.ink_colour, alert_type='low_stock', severity='warning', message='Resource "Colour Ink Cartridge" is low: 4 units remaining (reorder: 5).', resolved=False)
        Alert.objects.create(job=self.job6,  alert_type='abnormal_expense',  severity='warning',  message='Job "LAN Setup" expenses were approaching quoted price.', resolved=True, resolved_by=self.manager2, resolved_at=timezone.now()-timedelta(14))
        Alert.objects.create(job=self.job1,  alert_type='overdue_payment',   severity='warning',  message='Job "Business Cards — GoldLink Ventures" was completed 11 days ago. Outstanding: GHS 350.00.', resolved=False)
