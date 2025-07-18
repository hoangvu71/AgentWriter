"""
Input validation and sanitization utilities
"""
import re
import html
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException
import uuid

class ValidationError(Exception):
    """Custom validation error"""
    pass

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input by removing HTML tags and limiting length
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    # Remove HTML tags
    sanitized = html.escape(value)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    
    return sanitized.strip()

def validate_uuid(value: str) -> str:
    """
    Validate UUID format
    """
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValidationError(f"Invalid UUID format: {value}")

def validate_alphanumeric(value: str, max_length: int = 50) -> str:
    """
    Validate alphanumeric string with underscores and hyphens
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', value):
        raise ValidationError("Input must contain only alphanumeric characters, underscores, and hyphens")
    
    if len(value) > max_length:
        raise ValidationError(f"Input too long (max {max_length} characters)")
    
    return value

def validate_text_content(value: str, min_length: int = 1, max_length: int = 10000) -> str:
    """
    Validate text content for plots, authors, etc.
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    sanitized = sanitize_string(value, max_length)
    
    if len(sanitized) < min_length:
        raise ValidationError(f"Input too short (min {min_length} characters)")
    
    return sanitized

def validate_genre_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate genre-related data
    """
    required_fields = ['name']
    
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate name
    data['name'] = validate_text_content(data['name'], min_length=1, max_length=100)
    
    # Validate description if present
    if 'description' in data:
        data['description'] = validate_text_content(data['description'], min_length=0, max_length=500)
    
    return data

def validate_target_audience_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate target audience data
    """
    valid_age_groups = ['Children', 'Middle Grade', 'Young Adult', 'New Adult', 'Adult', 'Senior']
    valid_genders = ['All', 'Male', 'Female', 'Non-binary']
    valid_orientations = ['All', 'Heterosexual', 'LGBTQ+', 'Gay', 'Lesbian', 'Bisexual']
    
    # Validate age_group
    if 'age_group' in data:
        if data['age_group'] not in valid_age_groups:
            raise ValidationError(f"Invalid age group. Must be one of: {valid_age_groups}")
    
    # Validate gender
    if 'gender' in data:
        if data['gender'] not in valid_genders:
            raise ValidationError(f"Invalid gender. Must be one of: {valid_genders}")
    
    # Validate sexual_orientation
    if 'sexual_orientation' in data:
        if data['sexual_orientation'] not in valid_orientations:
            raise ValidationError(f"Invalid sexual orientation. Must be one of: {valid_orientations}")
    
    return data

# Pydantic models for request validation
class GenreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_name(cls, v):
        return sanitize_string(v, 100)
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return sanitize_string(v, 500)
        return v

class SubgenreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    genre_id: str = Field(..., min_length=1)
    
    @validator('name')
    def validate_name(cls, v):
        return sanitize_string(v, 100)
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return sanitize_string(v, 500)
        return v
    
    @validator('genre_id')
    def validate_genre_id(cls, v):
        return validate_uuid(v)

class MicrogenreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    subgenre_id: str = Field(..., min_length=1)
    
    @validator('name')
    def validate_name(cls, v):
        return sanitize_string(v, 100)
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return sanitize_string(v, 500)
        return v
    
    @validator('subgenre_id')
    def validate_subgenre_id(cls, v):
        return validate_uuid(v)

class TropeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_name(cls, v):
        return sanitize_string(v, 100)
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return sanitize_string(v, 500)
        return v

class ToneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('name')
    def validate_name(cls, v):
        return sanitize_string(v, 100)
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return sanitize_string(v, 500)
        return v

class TargetAudienceCreate(BaseModel):
    age_group: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., min_length=1, max_length=50)
    sexual_orientation: str = Field(..., min_length=1, max_length=50)
    
    @validator('age_group')
    def validate_age_group(cls, v):
        valid_values = ['Children', 'Middle Grade', 'Young Adult', 'New Adult', 'Adult', 'Senior']
        if v not in valid_values:
            raise ValueError(f"Invalid age group. Must be one of: {valid_values}")
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        valid_values = ['All', 'Male', 'Female', 'Non-binary']
        if v not in valid_values:
            raise ValueError(f"Invalid gender. Must be one of: {valid_values}")
        return v
    
    @validator('sexual_orientation')
    def validate_sexual_orientation(cls, v):
        valid_values = ['All', 'Heterosexual', 'LGBTQ+', 'Gay', 'Lesbian', 'Bisexual']
        if v not in valid_values:
            raise ValueError(f"Invalid sexual orientation. Must be one of: {valid_values}")
        return v

# Decorator for endpoint validation
def validate_endpoint(func):
    """
    Decorator to add validation to endpoints
    """
    def wrapper(*args, **kwargs):
        try:
            # Validate path parameters
            for key, value in kwargs.items():
                if key.endswith('_id') and isinstance(value, str):
                    kwargs[key] = validate_uuid(value)
                elif isinstance(value, str):
                    kwargs[key] = sanitize_string(value)
            
            return func(*args, **kwargs)
        except (ValidationError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return wrapper