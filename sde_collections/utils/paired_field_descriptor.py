class PairedFieldDescriptor:
    def __init__(self, field_name):
        self.manual_field_name = f"{field_name}_manual"
        self.ml_field_name = f"{field_name}_ml"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        # Return manual tag if available, otherwise ML tag
        manual_value = getattr(instance, self.manual_field_name, None)
        machine_learning_value = getattr(instance, self.ml_field_name, None)
        return manual_value if manual_value is not None else machine_learning_value

    def __set__(self, instance, value):
        # Set the value of the manual field
        setattr(instance, self.manual_field_name, value)

    def __delete__(self, instance):
        # Delete both manual and ML fields
        delattr(instance, self.manual_field_name)
        delattr(instance, self.ml_field_name)
