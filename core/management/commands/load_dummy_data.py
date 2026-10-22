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
    ResourceHistory, Purchase, PurchaseResource,
    Payment, Alert, Client, Receipt,
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
        self.create_clients()
        self.create_jobs()
        self.create_resource_usage()
        self.create_payments()
        self.create_alerts()
        self.stdout.write(self.style.SUCCESS('\n  Dummy data loaded successfully!\n'))
        self.stdout.write('   Sample accounts have unusable passwords; create a superuser with createsuperuser.\n')

    def create_users(self):
        self.stdout.write('  Creating users...')
        self.admin = User.objects.create_superuser(
            username='admin', password=None,
            first_name='Demo', last_name='Admin',
            email='admin@example.com', role='super_admin',
        )
        self.manager1 = User.objects.create_user(
            username='manager1', password=None,
            first_name='Demo', last_name='Manager One',
            email='manager1@example.com', role='manager',
        )
        self.manager2 = User.objects.create_user(
            username='manager2', password=None,
            first_name='Demo', last_name='Manager Two',
            email='manager2@example.com', role='manager',
        )
        self.staff1 = User.objects.create_user(username='staff1', password=None, first_name='Demo', last_name='Staff One', email='staff1@example.com', role='staff')
        self.staff2 = User.objects.create_user(username='staff2', password=None, first_name='Demo', last_name='Staff Two', email='staff2@example.com', role='staff')
        self.staff3 = User.objects.create_user(username='staff3', password=None, first_name='Demo', last_name='Staff Three', email='staff3@example.com', role='staff')
        self.staff4 = User.objects.create_user(username='staff4', password=None, first_name='Demo', last_name='Staff Four', email='staff4@example.com', role='staff')
        self.staff5 = User.objects.create_user(username='staff5', password=None, first_name='Demo', last_name='Staff Five', email='staff5@example.com', role='staff')
        self.staff6 = User.objects.create_user(username='staff6', password=None, first_name='Demo', last_name='Staff Six', email='staff6@example.com', role='staff')

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

    def create_clients(self):
        self.stdout.write('  Creating clients...')
        # One Client record per unique phone number across all jobs
        client_data = [
            ('0000000001', 'Demo Client 01'),
            ('0000000002', 'Demo Client 02'),
            ('0000000003', 'Demo Client 03'),
            ('0000000004', 'Demo Client 04'),
            ('0000000005', 'Demo Client 05'),
            ('0000000006', 'Demo Client 06'),
            ('0000000007', 'Demo Client 07'),
            ('0000000008', 'Demo Client 08'),
            ('0000000009', 'Demo Client 09'),
            ('0000000010', 'Demo Client 10'),
            ('0000000011', 'Demo Client 11'),
            ('0000000012', 'Demo Client 12'),
        ]
        for phone, name in client_data:
            Client.objects.create(phone=phone, name=name)

    def create_jobs(self):
        self.stdout.write('  Creating jobs...')
        today = timezone.now().date()

        self.job1  = Job.objects.create(title='Business Cards — Demo Client 01', department=self.dept_printing, service_type='printing', assigned_to=self.staff1, created_by=self.manager1, client_name='Demo Client 01', client_contact='0000000001', status='completed', priority='high', price=Decimal('350.00'), start_date=today-timedelta(14), due_date=today-timedelta(10), completed_at=timezone.now()-timedelta(11), description='500 double-sided business cards. Glossy finish, full colour.')
        self.job2  = Job.objects.create(title='Event Banner — Demo Client 02', department=self.dept_printing, service_type='printing', assigned_to=self.staff2, created_by=self.staff1, client_name='Demo Client 02', client_contact='0000000002', status='in_progress', priority='urgent', price=Decimal('800.00'), start_date=today-timedelta(3), due_date=today+timedelta(2), description='4 large-format vinyl banners (3m x 2m) for a graduation ceremony.')
        self.job3  = Job.objects.create(title='Flyer Printing — Demo Client 03', department=self.dept_printing, service_type='printing', assigned_to=self.staff1, created_by=self.manager1, client_name='Demo Client 03', client_contact='0000000003', status='pending', priority='medium', price=Decimal('420.00'), start_date=today, due_date=today+timedelta(5), description='1000 A5 full-colour flyers. Double-sided printing.')
        self.job4  = Job.objects.create(title='Laminated ID Cards — Demo Client 04', department=self.dept_printing, service_type='printing', assigned_to=self.staff2, created_by=self.manager1, client_name='Demo Client 04', client_contact='0000000004', status='on_hold', priority='low', price=Decimal('560.00'), start_date=today-timedelta(7), due_date=today-timedelta(2), description='200 laminated staff ID cards. Client yet to supply staff list and photos.')
        self.job5  = Job.objects.create(title='Brochure Design & Print — Demo Client 05', department=self.dept_printing, service_type='printing', assigned_to=self.staff1, created_by=self.staff2, client_name='Demo Client 05', client_contact='0000000005', status='cancelled', priority='medium', price=Decimal('670.00'), start_date=today-timedelta(20), due_date=today-timedelta(15), description='Tri-fold brochures for client services. Cancelled after a vendor change.')
        self.job6  = Job.objects.create(title='LAN Setup — Demo Client 06', department=self.dept_network, service_type='network_it', assigned_to=self.staff3, created_by=self.manager2, client_name='Demo Client 06', client_contact='0000000006', status='completed', priority='high', price=Decimal('2200.00'), start_date=today-timedelta(21), due_date=today-timedelta(14), completed_at=timezone.now()-timedelta(15), description='Full LAN installation for a 30-node computer lab.')
        self.job7  = Job.objects.create(title='WiFi Configuration — Demo Client 07', department=self.dept_network, service_type='network_it', assigned_to=self.staff4, created_by=self.staff3, client_name='Demo Client 07', client_contact='0000000007', status='in_progress', priority='high', price=Decimal('1500.00'), start_date=today-timedelta(4), due_date=today+timedelta(3), description='WiFi access point installation for a three-block residential estate.')
        self.job8  = Job.objects.create(title='Network Audit — Demo Client 08', department=self.dept_network, service_type='network_it', assigned_to=self.staff3, created_by=self.manager2, client_name='Demo Client 08', client_contact='0000000008', status='pending', priority='urgent', price=Decimal('3500.00'), start_date=today+timedelta(1), due_date=today+timedelta(6), description='Comprehensive network security audit for a branch office.')
        self.job9  = Job.objects.create(title='CCTV Network Integration — Demo Client 09', department=self.dept_network, service_type='network_it', assigned_to=self.staff4, created_by=self.manager2, client_name='Demo Client 09', client_contact='0000000009', status='pending', priority='medium', price=Decimal('1800.00'), start_date=today-timedelta(1), due_date=today-timedelta(1), description='Connect 16 CCTV cameras to a central NVR system.')
        self.job10 = Job.objects.create(title='Corporate Photography — Demo Client 10', department=self.dept_multimedia, service_type='multimedia', assigned_to=self.staff5, created_by=self.manager1, client_name='Demo Client 10', client_contact='0000000010', status='completed', priority='high', price=Decimal('1200.00'), start_date=today-timedelta(10), due_date=today-timedelta(7), completed_at=timezone.now()-timedelta(8), description='Executive headshots and team photography for 25 staff members.')
        self.job11 = Job.objects.create(title='Product Video — Demo Client 11', department=self.dept_multimedia, service_type='multimedia', assigned_to=self.staff6, created_by=self.staff5, client_name='Demo Client 11', client_contact='0000000011', status='in_progress', priority='high', price=Decimal('2500.00'), start_date=today-timedelta(5), due_date=today+timedelta(4), description='60-second promotional product video with post-production editing.')
        self.job12 = Job.objects.create(title='Graphic Design — Demo Client 12', department=self.dept_multimedia, service_type='multimedia', assigned_to=self.staff5, created_by=self.manager1, client_name='Demo Client 12', client_contact='0000000012', status='pending', priority='urgent', price=Decimal('1800.00'), start_date=today, due_date=today+timedelta(3), description='Digital billboard and social media assets with 12 design variants.')

        self.stdout.write('  Creating job timeline updates...')
        JobUpdate.objects.create(job=self.job1,  updated_by=self.manager1, status='pending',     comment='Job created and assigned to a staff member.')
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
        JobUpdate.objects.create(job=self.job6,  updated_by=self.staff3,   status='completed',   comment='All 30 nodes connected and tested. Client approved the work.')
        JobUpdate.objects.create(job=self.job9,  updated_by=self.manager2, status='pending',     comment='Job registered. Due date already passed — client delayed approval.')
        JobUpdate.objects.create(job=self.job10, updated_by=self.manager1, status='pending',     comment='Job created.')
        JobUpdate.objects.create(job=self.job10, updated_by=self.staff5,   status='in_progress', comment='On-location shoot complete. Studio session scheduled.')
        JobUpdate.objects.create(job=self.job10, updated_by=self.staff5,   status='completed',   comment='All photos edited and delivered to the client.')
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

    def create_payments(self):
        self.stdout.write('  Creating payments and receipts...')
        # job6 — LAN Setup, completed, fully paid
        p6 = Payment.objects.create(
            job=self.job6, amount=Decimal('2200.00'),
            payment_date=self.job6.completed_at.date(),
            payment_method='mobile_money', reference='MM-290487',
            notes='Full payment received on completion.',
            recorded_by=self.manager2,
        )
        Receipt.objects.create(payment=p6)

        # job10 — Corporate Photography, completed, fully paid
        p10 = Payment.objects.create(
            job=self.job10, amount=Decimal('1200.00'),
            payment_date=self.job10.completed_at.date(),
            payment_method='bank_transfer', reference='BT-881023',
            notes='Full payment via bank transfer.',
            recorded_by=self.manager1,
        )
        Receipt.objects.create(payment=p10)

        # job1 — Business Cards, completed, no payment (drives overdue_payment alert)

    def create_alerts(self):
        self.stdout.write('  Creating alerts...')
        Alert.objects.create(job=self.job9,  alert_type='overdue_job',      severity='critical', message='Job "CCTV Network Integration — Demo Client 09" (#9) is overdue.', resolved=False)
        Alert.objects.create(job=self.job4,  alert_type='overdue_job',      severity='warning',  message='Job "Laminated ID Cards — Demo Client 04" (#4) is on hold and past its due date.', resolved=False)
        Alert.objects.create(resource=self.laminate,   alert_type='low_stock', severity='warning', message='Resource "Lamination Film (A4)" is low: 3 rolls remaining (reorder: 4).', resolved=False)
        Alert.objects.create(resource=self.ink_colour, alert_type='low_stock', severity='warning', message='Resource "Colour Ink Cartridge" is low: 4 units remaining (reorder: 5).', resolved=False)
        Alert.objects.create(job=self.job6,  alert_type='abnormal_expense',  severity='warning',  message='Job "LAN Setup" expenses were approaching quoted price.', resolved=True, resolved_by=self.manager2, resolved_at=timezone.now()-timedelta(14))
        Alert.objects.create(job=self.job1,  alert_type='overdue_payment',   severity='warning',  message='Job "Business Cards — Demo Client 01" was completed 11 days ago. Outstanding: GHS 350.00.', resolved=False)
