"""
Drug Interactions Services
Core services for drug interaction checking and clinical decision support.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import DrugInteraction, InteractionCheck, DrugAllergy, InteractionSeverity

logger = logging.getLogger(__name__)
User = get_user_model()


class DrugInteractionService:
    """Service for checking drug interactions and managing clinical decision support."""
    
    def __init__(self):
        """Initialize the drug interaction service."""
        self.severity_weights = {
            InteractionSeverity.MINOR: 1,
            InteractionSeverity.MODERATE: 2,
            InteractionSeverity.MAJOR: 3,
            InteractionSeverity.CONTRAINDICATED: 4
        }
    
    def check_drug_interactions(
        self,
        medications: List[str],
        patient_id: Optional[int] = None,
        checked_by_id: Optional[int] = None,
        include_allergies: bool = True
    ) -> Dict:
        """
        Check for drug interactions among a list of medications.
        
        Args:
            medications: List of medication names
            patient_id: Optional patient ID for allergy checking
            checked_by_id: ID of user performing the check
            include_allergies: Whether to include allergy checks
            
        Returns:
            Dictionary containing interaction results
        """
        start_time = timezone.now()
        
        try:
            interactions_found = []
            allergy_alerts = []
            
            # Check drug-drug interactions
            for i, med1 in enumerate(medications):
                for med2 in medications[i+1:]:
                    interactions = self._find_interactions_between_drugs(med1, med2)
                    interactions_found.extend(interactions)
            
            # Check for drug allergies if patient provided
            if include_allergies and patient_id:
                allergy_alerts = self._check_drug_allergies(medications, patient_id)
            
            # Calculate severity statistics
            severity_counts = {
                'minor': 0,
                'moderate': 0,
                'major': 0,
                'contraindicated': 0
            }
            
            for interaction in interactions_found:
                severity_counts[interaction.severity] += 1
            
            # Calculate check duration
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            # Create interaction check record
            check_record = None
            if checked_by_id:
                check_record = InteractionCheck.objects.create(
                    checked_by_id=checked_by_id,
                    patient_id=patient_id,
                    medications_checked=medications,
                    total_interactions=len(interactions_found),
                    major_interactions=severity_counts['major'],
                    contraindicated_interactions=severity_counts['contraindicated'],
                    check_duration_ms=duration_ms,
                    data_source="internal"
                )
                
                # Add found interactions to the check record
                check_record.interactions_found.set(interactions_found)
            
            # Generate clinical recommendations
            recommendations = self._generate_clinical_recommendations(
                interactions_found, allergy_alerts
            )
            
            result = {
                'success': True,
                'check_id': str(check_record.id) if check_record else None,
                'medications_checked': medications,
                'total_interactions': len(interactions_found),
                'interactions': [
                    {
                        'id': str(interaction.id),
                        'drug1': interaction.drug_name_1,
                        'drug2': interaction.drug_name_2,
                        'severity': interaction.severity,
                        'type': interaction.interaction_type,
                        'mechanism': interaction.mechanism,
                        'clinical_effects': interaction.clinical_effects,
                        'management': interaction.management,
                        'confidence': interaction.confidence_level
                    }
                    for interaction in interactions_found
                ],
                'severity_counts': severity_counts,
                'allergy_alerts': [
                    {
                        'drug': allergy.drug_name,
                        'severity': allergy.severity,
                        'reaction': allergy.reaction_description,
                        'symptoms': allergy.symptoms
                    }
                    for allergy in allergy_alerts
                ],
                'recommendations': recommendations,
                'check_duration_ms': duration_ms,
                'timestamp': start_time.isoformat()
            }
            
            logger.info(f"Drug interaction check completed: {len(interactions_found)} interactions found")
            return result
            
        except Exception as e:
            logger.error(f"Drug interaction check failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'medications_checked': medications,
                'total_interactions': 0,
                'interactions': [],
                'allergy_alerts': [],
                'recommendations': []
            }
    
    def _find_interactions_between_drugs(self, drug1: str, drug2: str) -> List[DrugInteraction]:
        """Find interactions between two specific drugs."""
        interactions = DrugInteraction.objects.filter(
            Q(
                (Q(drug_name_1__icontains=drug1) | Q(generic_name_1__icontains=drug1)) &
                (Q(drug_name_2__icontains=drug2) | Q(generic_name_2__icontains=drug2))
            ) |
            Q(
                (Q(drug_name_1__icontains=drug2) | Q(generic_name_1__icontains=drug2)) &
                (Q(drug_name_2__icontains=drug1) | Q(generic_name_2__icontains=drug1))
            ),
            is_active=True
        ).order_by('-severity')
        
        return list(interactions)
    
    def _check_drug_allergies(self, medications: List[str], patient_id: int) -> List[DrugAllergy]:
        """Check for drug allergies for a specific patient."""
        try:
            patient_allergies = DrugAllergy.objects.filter(
                patient_id=patient_id,
                is_active=True
            )
            
            allergy_alerts = []
            
            for medication in medications:
                # Direct drug name matches
                direct_matches = patient_allergies.filter(
                    Q(drug_name__icontains=medication) | 
                    Q(generic_name__icontains=medication)
                )
                allergy_alerts.extend(direct_matches)
                
                # Cross-reactive drug checks
                for allergy in patient_allergies:
                    if any(cross_drug.lower() in medication.lower() 
                           for cross_drug in allergy.cross_reactive_drugs):
                        allergy_alerts.append(allergy)
            
            return list(set(allergy_alerts))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Failed to check drug allergies: {e}")
            return []
    
    def _generate_clinical_recommendations(
        self, 
        interactions: List[DrugInteraction],
        allergies: List[DrugAllergy]
    ) -> List[Dict]:
        """Generate clinical recommendations based on interactions and allergies."""
        recommendations = []
        
        # Handle contraindicated interactions
        contraindicated = [i for i in interactions if i.severity == InteractionSeverity.CONTRAINDICATED]
        if contraindicated:
            recommendations.append({
                'type': 'contraindication',
                'priority': 'critical',
                'title': _('Contraindicated Drug Combination'),
                'message': _('One or more drug combinations are contraindicated and should not be used together.'),
                'actions': [_('Consider alternative medications'), _('Consult clinical pharmacist')]
            })
        
        # Handle major interactions
        major = [i for i in interactions if i.severity == InteractionSeverity.MAJOR]
        if major:
            recommendations.append({
                'type': 'major_interaction',
                'priority': 'high',
                'title': _('Major Drug Interactions'),
                'message': _('Major interactions detected that may cause significant clinical effects.'),
                'actions': [_('Monitor closely'), _('Consider dose adjustments'), _('Evaluate risk vs benefit')]
            })
        
        # Handle severe allergies
        severe_allergies = [a for a in allergies if a.severity in ['severe', 'life_threatening']]
        if severe_allergies:
            recommendations.append({
                'type': 'severe_allergy',
                'priority': 'critical',
                'title': _('Severe Allergy Alert'),
                'message': _('Patient has severe allergies to prescribed medications.'),
                'actions': [_('Do not administer'), _('Find alternative medications'), _('Update allergy records')]
            })
        
        # General monitoring recommendations
        if interactions or allergies:
            recommendations.append({
                'type': 'monitoring',
                'priority': 'medium',
                'title': _('Enhanced Monitoring Required'),
                'message': _('Enhanced patient monitoring is recommended due to identified interactions or allergies.'),
                'actions': [_('Schedule follow-up'), _('Monitor for adverse effects'), _('Patient education')]
            })
        
        return recommendations
    
    def add_drug_interaction(
        self, 
        interaction_data: Dict,
        reviewed_by_id: Optional[int] = None
    ) -> DrugInteraction:
        """
        Add a new drug interaction to the database.
        
        Args:
            interaction_data: Dictionary containing interaction information
            reviewed_by_id: ID of clinical reviewer
            
        Returns:
            Created DrugInteraction instance
        """
        try:
            interaction = DrugInteraction.objects.create(
                drug_name_1=interaction_data['drug_name_1'],
                drug_name_2=interaction_data['drug_name_2'],
                generic_name_1=interaction_data.get('generic_name_1', ''),
                generic_name_2=interaction_data.get('generic_name_2', ''),
                interaction_type=interaction_data['interaction_type'],
                severity=interaction_data['severity'],
                mechanism=interaction_data['mechanism'],
                clinical_effects=interaction_data['clinical_effects'],
                management=interaction_data['management'],
                confidence_level=interaction_data.get('confidence_level', 1.0),
                evidence_level=interaction_data.get('evidence_level', ''),
                references=interaction_data.get('references', []),
                monitoring_parameters=interaction_data.get('monitoring_parameters', []),
                reviewed_by_id=reviewed_by_id,
                reviewed_at=timezone.now() if reviewed_by_id else None
            )
            
            logger.info(f"Added new drug interaction: {interaction.drug_name_1} + {interaction.drug_name_2}")
            return interaction
            
        except Exception as e:
            logger.error(f"Failed to add drug interaction: {e}")
            raise
    
    def add_drug_allergy(
        self,
        patient_id: int,
        allergy_data: Dict,
        reported_by_id: Optional[int] = None
    ) -> DrugAllergy:
        """
        Add a drug allergy for a patient.
        
        Args:
            patient_id: ID of the patient
            allergy_data: Dictionary containing allergy information
            reported_by_id: ID of user reporting the allergy
            
        Returns:
            Created DrugAllergy instance
        """
        try:
            allergy = DrugAllergy.objects.create(
                patient_id=patient_id,
                drug_name=allergy_data['drug_name'],
                generic_name=allergy_data.get('generic_name', ''),
                drug_class=allergy_data.get('drug_class', ''),
                allergy_type=allergy_data['allergy_type'],
                severity=allergy_data['severity'],
                reaction_description=allergy_data['reaction_description'],
                symptoms=allergy_data.get('symptoms', []),
                onset_time=allergy_data.get('onset_time', ''),
                date_of_reaction=allergy_data.get('date_of_reaction'),
                reported_by_id=reported_by_id,
                cross_reactive_drugs=allergy_data.get('cross_reactive_drugs', [])
            )
            
            logger.info(f"Added drug allergy for patient {patient_id}: {allergy.drug_name}")
            return allergy
            
        except Exception as e:
            logger.error(f"Failed to add drug allergy: {e}")
            raise
    
    def get_patient_interaction_history(self, patient_id: int, days: int = 90) -> Dict:
        """
        Get interaction check history for a patient.
        
        Args:
            patient_id: ID of the patient
            days: Number of days to look back
            
        Returns:
            Dictionary containing interaction history
        """
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            
            checks = InteractionCheck.objects.filter(
                patient_id=patient_id,
                created_at__gte=cutoff_date
            ).order_by('-created_at')
            
            # Calculate statistics
            total_checks = checks.count()
            total_interactions = sum(check.total_interactions for check in checks)
            major_interactions = sum(check.major_interactions for check in checks)
            contraindicated = sum(check.contraindicated_interactions for check in checks)
            
            # Get current allergies
            current_allergies = DrugAllergy.objects.filter(
                patient_id=patient_id,
                is_active=True
            ).order_by('-severity')
            
            return {
                'patient_id': patient_id,
                'period_days': days,
                'total_checks': total_checks,
                'total_interactions_found': total_interactions,
                'major_interactions': major_interactions,
                'contraindicated_interactions': contraindicated,
                'recent_checks': [
                    {
                        'id': str(check.id),
                        'date': check.created_at.date(),
                        'medications': check.medications_checked,
                        'interactions_found': check.total_interactions,
                        'checked_by': check.checked_by.get_full_name()
                    }
                    for check in checks[:10]  # Last 10 checks
                ],
                'current_allergies': [
                    {
                        'drug': allergy.drug_name,
                        'severity': allergy.severity,
                        'type': allergy.allergy_type,
                        'verified': allergy.is_verified
                    }
                    for allergy in current_allergies
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get patient interaction history: {e}")
            return {
                'patient_id': patient_id,
                'error': str(e),
                'total_checks': 0,
                'recent_checks': [],
                'current_allergies': []
            }
    
    def get_interaction_statistics(self) -> Dict:
        """Get system-wide interaction statistics."""
        try:
            # Interaction database statistics
            total_interactions = DrugInteraction.objects.filter(is_active=True).count()
            
            interactions_by_severity = {}
            for severity in InteractionSeverity.choices:
                count = DrugInteraction.objects.filter(
                    is_active=True,
                    severity=severity[0]
                ).count()
                interactions_by_severity[severity[0]] = count
            
            # Check statistics (last 30 days)
            recent_checks = InteractionCheck.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            )
            
            total_recent_checks = recent_checks.count()
            avg_interactions_per_check = (
                recent_checks.aggregate(avg=models.Avg('total_interactions'))['avg'] or 0
            )
            
            # Top interacting drugs
            top_drugs = []
            # This would require more complex aggregation in a real implementation
            
            return {
                'database_stats': {
                    'total_interactions': total_interactions,
                    'by_severity': interactions_by_severity
                },
                'usage_stats': {
                    'checks_last_30_days': total_recent_checks,
                    'avg_interactions_per_check': round(avg_interactions_per_check, 2)
                },
                'top_interacting_drugs': top_drugs
            }
            
        except Exception as e:
            logger.error(f"Failed to get interaction statistics: {e}")
            return {'error': str(e)}
    
    def validate_interaction_data(self, interaction_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate interaction data before adding to database.
        
        Args:
            interaction_data: Dictionary containing interaction information
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required_fields = ['drug_name_1', 'drug_name_2', 'severity', 'mechanism', 'clinical_effects']
        for field in required_fields:
            if not interaction_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate severity
        if interaction_data.get('severity') not in [choice[0] for choice in InteractionSeverity.choices]:
            errors.append("Invalid severity level")
        
        # Validate confidence level
        confidence = interaction_data.get('confidence_level', 1.0)
        if not (0.0 <= confidence <= 1.0):
            errors.append("Confidence level must be between 0.0 and 1.0")
        
        # Check for duplicate
        if interaction_data.get('drug_name_1') and interaction_data.get('drug_name_2'):
            existing = DrugInteraction.objects.filter(
                drug_name_1=interaction_data['drug_name_1'],
                drug_name_2=interaction_data['drug_name_2'],
                interaction_type=interaction_data.get('interaction_type', 'drug_drug')
            ).exists()
            
            if existing:
                errors.append("Interaction already exists in database")
        
        return len(errors) == 0, errors
