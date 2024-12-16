# Paired Field Descriptor System

## Overview

The Paired Field Descriptor is a Django model descriptor designed to manage fields with both manual and machine learning (ML) generated variants. This system provides a flexible approach to handling metadata fields, with a focus on tag management and priority handling.

## Core Concepts

### Field Pairing Mechanism
The descriptor automatically creates two associated fields for each defined descriptor:
- **Manual Field**: Manually entered or curated metadata
- **ML Field**: Machine learning generated metadata

### Key Characteristics
- Manual field takes precedence over ML field
- Flexible field type support
- Handles empty arrays and None values
- Requires explicit setting of ML fields

## Implementation

### Creating a Paired Field Descriptor

```python
tdamm_tag = PairedFieldDescriptor(
    field_name="tdamm_tag",
    field_type=ArrayField(models.CharField(max_length=255, choices=TDAMMTags.choices), blank=True, null=True),
    verbose_name="TDAMM Tags",
)
```

#### Parameters
- `field_name`: Base name for the descriptor
- `field_type`: Django field type (supports various field types)
- `verbose_name`: Optional human-readable name

### Field Naming Convention
When you define a descriptor, two additional fields are automatically created:
- `{field_name}_manual`: For manually entered values
- `{field_name}_ml`: For machine learning generated values

## Characteristics

### Field Priority
1. Manual field always takes precedence
2. ML field serves as a fallback
3. Empty manual fields or None values defer to ML field

### Field Retrieval
```python
# Retrieval automatically prioritizes manual field
tags = url.tdamm_tag  # Returns manual tags if exist, otherwise ML tags
```

### Field Setting
```python
# Sets only the manual field
url.tdamm_tag = ["MMA_M_EM", "MMA_M_G"]

# ML field must be set explicitly
url.tdamm_tag_ml = ["MMA_O_BH"]
```

### Field Deletion
```python
# Deletes both manual and ML fields
del url.tdamm_tag
```

### Data Preservation
- Paired fields maintain their state during:
  - Dump to Delta migration
  - Delta to Curated promotion
- Manual entries take precedence in all migration stages

## Serializer Integration

Here's the way to configure the serializer to retrieve the paired field, seamlessly extracting either manual or ML tags based on the descriptor's priority rules.
```python
class DeltaUrlSerializer(serializers.ModelSerializer):
    tdamm_tag = serializers.SerializerMethodField()

    class Meta:
        model = DeltaUrl
        fields = ("url", "tdamm_tag")

    def get_tdamm_tag(self, obj):
        tags = obj.tdamm_tag
        return tags if tags is not None else []
```
