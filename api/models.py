from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('agent', 'Agent'),
        ('supervisor', 'Supervisor'),
        ('manager', 'Manager'),
    )
    
    # Kenya's 47 counties
    COUNTY_CHOICES = (
        ('nairobi', 'Nairobi'),
        ('mombasa', 'Mombasa'),
        ('kwale', 'Kwale'),
        ('kilifi', 'Kilifi'),
        ('tana_river', 'Tana River'),
        ('lamu', 'Lamu'),
        ('taita_taveta', 'Taita Taveta'),
        ('garissa', 'Garissa'),
        ('wajir', 'Wajir'),
        ('mandera', 'Mandera'),
        ('marsabit', 'Marsabit'),
        ('isiolo', 'Isiolo'),
        ('meru', 'Meru'),
        ('tharaka_nithi', 'Tharaka-Nithi'),
        ('embu', 'Embu'),
        ('kitui', 'Kitui'),
        ('machakos', 'Machakos'),
        ('makueni', 'Makueni'),
        ('nyandarua', 'Nyandarua'),
        ('nyeri', 'Nyeri'),
        ('kirinyaga', 'Kirinyaga'),
        ('muranga', "Murang'a"),
        ('kiambu', 'Kiambu'),
        ('turkana', 'Turkana'),
        ('west_pokot', 'West Pokot'),
        ('samburu', 'Samburu'),
        ('trans_nzoia', 'Trans Nzoia'),
        ('uasin_gishu', 'Uasin Gishu'),
        ('elgeyo_marakwet', 'Elgeyo-Marakwet'),
        ('nandi', 'Nandi'),
        ('baringo', 'Baringo'),
        ('laikipia', 'Laikipia'),
        ('nakuru', 'Nakuru'),
        ('narok', 'Narok'),
        ('kajiado', 'Kajiado'),
        ('kericho', 'Kericho'),
        ('bomet', 'Bomet'),
        ('kakamega', 'Kakamega'),
        ('vihiga', 'Vihiga'),
        ('bungoma', 'Bungoma'),
        ('busia', 'Busia'),
        ('siaya', 'Siaya'),
        ('kisumu', 'Kisumu'),
        ('homa_bay', 'Homa Bay'),
        ('migori', 'Migori'),
        ('kisii', 'Kisii'),
        ('nyamira', 'Nyamira'),
    )
    
    SUBLOCATION_CHOICES = (
        ('central', 'Central'),
        ('east', 'East'),
        ('west', 'West'),
        ('north', 'North'),
        ('south', 'South'),
        ('urban', 'Urban'),
        ('rural', 'Rural'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    county = models.CharField(max_length=50, choices=COUNTY_CHOICES)
    sublocation = models.CharField(max_length=50, choices=SUBLOCATION_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.employee_id and self.role in ['agent', 'supervisor']:
            # Generate unique employee ID
            prefix = 'AGT' if self.role == 'agent' else 'SUP'
            self.employee_id = f"{prefix}{uuid.uuid4().hex[:8].upper()}"
            # Set username and password to employee_id for initial login
            if not self.username:
                self.username = self.employee_id
            if not self.password:
                self.set_password(self.employee_id)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name() or self.username}"

class Report(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    county = models.CharField(max_length=50, choices=CustomUser.COUNTY_CHOICES)
    sublocation = models.CharField(max_length=50, choices=CustomUser.SUBLOCATION_CHOICES)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='assigned_reports')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Auto-calculated fields
    total_entries = models.IntegerField(default=0)
    active_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Editable field
    manager_feedback = models.TextField(blank=True)
    
    def update_calculated_fields(self):
        """Update auto-calculated fields based on report data"""
        data_rows = self.data_rows.all()
        if data_rows.exists():
            self.total_entries = data_rows.count()
            active_count = data_rows.filter(is_active=True).count()
            completed_count = data_rows.filter(status='completed').count()
            
            self.active_rate = (active_count / self.total_entries) * 100 if self.total_entries > 0 else 0
            self.completion_rate = (completed_count / self.total_entries) * 100 if self.total_entries > 0 else 0
            self.save()
    
    def __str__(self):
        return f"{self.title} - {self.county}"

class ReportData(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='data_rows')
    entry_number = models.CharField(max_length=50, unique=True)
    
    # Locked fields (basic information)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    location = models.CharField(max_length=200)
    
    # Auto-calculated fields
    is_active = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Dropdown fields
    service_type = models.CharField(max_length=50, choices=[
        ('installation', 'Installation'),
        ('maintenance', 'Maintenance'),
        ('repair', 'Repair'),
        ('upgrade', 'Upgrade'),
        ('consultation', 'Consultation'),
    ])
    
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ])
    
    # Editable feedback fields
    agent_feedback = models.TextField(blank=True)
    supervisor_feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['report', 'entry_number']
    
    def save(self, *args, **kwargs):
        # Auto-generate entry number if not provided
        if not self.entry_number:
            last_entry = ReportData.objects.filter(report=self.report).order_by('-id').first()
            last_num = int(last_entry.entry_number.split('-')[-1]) if last_entry else 0
            self.entry_number = f"{self.report.id}-ENT-{last_num + 1:04d}"
        
        # Auto-calculate is_active based on status
        self.is_active = self.status in ['in_progress', 'completed']
        
        super().save(*args, **kwargs)
        # Update parent report calculated fields
        self.report.update_calculated_fields()
    
    def __str__(self):
        return f"{self.entry_number} - {self.customer_name}"