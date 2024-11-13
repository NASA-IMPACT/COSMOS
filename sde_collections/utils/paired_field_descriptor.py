from django.db import models
from django.contrib.postgres.fields import ArrayField

class PairedFieldDescriptor:
    """
    A descriptor that manages paired manual/ML fields where:
    - Setting the main field only affects the manual field
    - ML field must be set explicitly
    - Getting the main field returns manual if present, otherwise ML
    """
    
    def __init__(self, field_name, field_type, switch, verbose_name=""):
        self.field_name = field_name
        self.manual_field_name = f"{field_name}_manual"
        self.ml_field_name = f"{field_name}_ml"
        self.field_type = field_type
        self.verbose_name = verbose_name or field_name.replace('_', ' ').title()
        self.switch = switch

    def contribute_to_class(self, cls, name):
        """Called by Django when the descriptor is added to the model class."""
        # Create manual field
        manual_field = self._create_field(
            verbose_name=f"{self.verbose_name} Manual",
            db_column=self.manual_field_name
        )
        
        # Create ML field
        ml_field = self._create_field(
            verbose_name=f"{self.verbose_name} ML",
            db_column=self.ml_field_name
        )

        # Add fields to the model's _meta
        cls.add_to_class(self.manual_field_name, manual_field)
        cls.add_to_class(self.ml_field_name, ml_field)

        # Store the descriptor
        setattr(cls, name, self)

    def _create_field(self, verbose_name, db_column):
        """Helper method to create a new field instance with the right configuration"""
        if isinstance(self.field_type, type):
            # If field_type is a class, instantiate it
            field = self.field_type()
        else:
            # If field_type is already an instance, clone it
            field = self.field_type.clone()
        
        field.verbose_name = verbose_name
        field.db_column = db_column
        
        return field

    def __get__(self, instance, owner):
        """
        Get the value of the main field:
        - Returns manual tags if they exist
        - Otherwise returns ML tags
        - Returns None if switch is False
        """
        if instance is None:
            return self
        
        if not getattr(instance, self.switch , False):
            return None

        manual_value = getattr(instance, self.manual_field_name, None)
        ml_value = getattr(instance, self.ml_field_name, None)
        
        # Return manual if it exists, otherwise ML
        return manual_value if manual_value is not None else ml_value

    def __set__(self, instance, value):
        """
        Set only the manual field when setting the field.
        ML field must be set explicitly.
        """
        if getattr(instance, self.switch, False):
            # Only set the manual field
            setattr(instance, self.manual_field_name, value)

    def __delete__(self, instance):
        """Delete both manual and ML fields"""
        setattr(instance, self.manual_field_name, None)
        setattr(instance, self.ml_field_name, None)

    def set_ml(self, instance, value):
        """Explicit method to set ML tags"""
        if getattr(instance, self.switch, False):
            setattr(instance, self.ml_field_name, value)