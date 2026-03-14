"""
Validation schema for user accessibility preferences.

Handles validation for font size, contrast modes, motion reduction,
and assistive technology settings.
"""

from marshmallow import Schema, fields, validate, post_load


class AccessibilityPreferencesSchema(Schema):
    """Validation schema for accessibility preferences."""
    
    font_size_multiplier = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0.8, max=2.0)
    )
    
    text_spacing_increased = fields.Boolean(required=False, allow_none=True)
    high_contrast_mode = fields.Boolean(required=False, allow_none=True)
    color_blind_mode = fields.Boolean(required=False, allow_none=True)
    reduced_motion = fields.Boolean(required=False, allow_none=True)
    screen_reader_optimized = fields.Boolean(required=False, allow_none=True)
    keyboard_navigation_enhanced = fields.Boolean(required=False, allow_none=True)
    focus_indicators_enhanced = fields.Boolean(required=False, allow_none=True)
    
    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values for accessibility preferences."""
        data.setdefault('font_size_multiplier', 1.0)
        data.setdefault('text_spacing_increased', False)
        data.setdefault('high_contrast_mode', False)
        data.setdefault('color_blind_mode', False)
        data.setdefault('reduced_motion', False)
        data.setdefault('screen_reader_optimized', False)
        data.setdefault('keyboard_navigation_enhanced', False)
        data.setdefault('focus_indicators_enhanced', False)
        return data
