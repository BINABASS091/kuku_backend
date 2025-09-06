from django.db import models
from django.utils.translation import gettext_lazy as _


class PatientHealth(models.Model):
    """
    Represents a health condition that a patient might have.
    Used to track exceptions for recommendations.
    """
    description = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Description of the health condition (e.g., Diabetes, Hypertension)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient Health Condition"
        verbose_name_plural = "Patient Health Conditions"
        ordering = ['description']

    def __str__(self):
        return self.description


class Recommendation(models.Model):
    """
    Represents a medical recommendation that can be associated with anomalies.
    """
    class RecoType(models.TextChoices):
        TEMPERATURE = 'Temperature', _('Temperature')
        SPO2 = 'Spo2', _('Blood Oxygen')
        HEART = 'Heart', _('Heart Rate')
        RESPIRATION = 'Respiration', _('Respiration')
        PRESSURE = 'Pressure', _('Blood Pressure')
        OTHER = 'Other', _('Other')
    
    class Context(models.TextChoices):
        HOME = 'Home', _('Home')
        HOSPITAL = 'Hospital', _('Hospital')
        AMBULATORY = 'Ambulatory', _('Ambulatory')
        ANY = 'Any', _('Any')
    
    description = models.CharField(
        max_length=200, 
        unique=True,
        help_text="Detailed description of the recommendation"
    )
    reco_type = models.CharField(
        max_length=20, 
        choices=RecoType.choices,
        help_text="Type of recommendation based on vital sign"
    )
    context = models.CharField(
        max_length=20, 
        choices=Context.choices, 
        default=Context.ANY,
        help_text="Context in which this recommendation applies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['reco_type', 'description']
        indexes = [
            models.Index(fields=['reco_type']),
            models.Index(fields=['context']),
        ]

    def __str__(self):
        return f"{self.get_reco_type_display()}: {self.description}"


class ExceptionDisease(models.Model):
    """
    Represents an exception where a recommendation should not be applied
    for patients with specific health conditions.
    """
    recommendation = models.ForeignKey(
        'knowledge.Recommendation', 
        on_delete=models.CASCADE, 
        related_name='exceptions',
        help_text="The recommendation that has an exception"
    )
    health = models.ForeignKey(
        'knowledge.PatientHealth', 
        on_delete=models.CASCADE, 
        related_name='exceptions',
        help_text="The health condition that triggers this exception"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Disease Exception"
        verbose_name_plural = "Disease Exceptions"
        unique_together = ('recommendation', 'health')
        ordering = ['recommendation__reco_type', 'health__description']
    
    def __str__(self):
        return f"{self.recommendation} - Exception for {self.health}"


class Anomaly(models.Model):
    """
    Represents an anomaly detected in patient monitoring data.
    Each ID field corresponds to a specific type of anomaly detection.
    """
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        RESOLVED = 'resolved', _('Resolved')
    
    hr_id = models.IntegerField(
        verbose_name="Heart Rate Anomaly ID",
        help_text="Reference ID for heart rate anomaly detection"
    )
    sp_id = models.IntegerField(
        verbose_name="Blood Oxygen Anomaly ID",
        help_text="Reference ID for blood oxygen anomaly detection"
    )
    pr_id = models.IntegerField(
        verbose_name="Pulse Rate Anomaly ID",
        help_text="Reference ID for pulse rate anomaly detection"
    )
    bt_id = models.IntegerField(
        verbose_name="Body Temperature Anomaly ID",
        help_text="Reference ID for body temperature anomaly detection"
    )
    resp_id = models.IntegerField(
        verbose_name="Respiration Anomaly ID",
        help_text="Reference ID for respiration rate anomaly detection"
    )
    status = models.BooleanField(
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Whether this anomaly is currently active or resolved"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Anomalies"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hr_id', 'sp_id', 'pr_id', 'bt_id', 'resp_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        active = "Active" if self.status else "Resolved"
        return f"Anomaly {self.id} ({active}) - Detected on {self.created_at.strftime('%Y-%m-%d')}"


class Medication(models.Model):
    """
    Represents a medication or treatment recommendation for a specific anomaly.
    Tracks the sequence of medications to be administered.
    """
    diagnosis = models.ForeignKey(
        'knowledge.Anomaly', 
        on_delete=models.CASCADE, 
        related_name='medications',
        help_text="The anomaly diagnosis this medication is for"
    )
    recommendation = models.ForeignKey(
        'knowledge.Recommendation', 
        on_delete=models.PROTECT, 
        related_name='medications',
        help_text="The recommended treatment or medication"
    )
    user = models.ForeignKey(
        'accounts.User', 
        on_delete=models.PROTECT, 
        related_name='medications',
        help_text="The healthcare provider who prescribed this medication"
    )
    sequence_no = models.PositiveSmallIntegerField(
        default=1,
        help_text="The order in which this medication should be administered"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes or instructions for this medication"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['diagnosis', 'sequence_no']
        unique_together = ('diagnosis', 'recommendation')
        indexes = [
            models.Index(fields=['diagnosis', 'sequence_no']),
            models.Index(fields=['sequence_no']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(sequence_no__gt=0),
                name='sequence_no_positive'
            )
        ]
    
    def __str__(self):
        return f"{self.sequence_no}. {self.recommendation} for {self.diagnosis}"
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure sequence numbers are updated correctly.
        """
        if not self.pk:  # Only on creation
            # Get the max sequence number for this diagnosis and add 1
            max_seq = Medication.objects.filter(
                diagnosis=self.diagnosis
            ).aggregate(models.Max('sequence_no'))['sequence_no__max'] or 0
            self.sequence_no = max_seq + 1
        super().save(*args, **kwargs)

# Create your models here.
