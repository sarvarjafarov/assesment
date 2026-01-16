from django import forms
from .models import DemoRequest


class DemoRequestForm(forms.ModelForm):
    """Form for capturing demo requests from the homepage."""

    class Meta:
        model = DemoRequest
        fields = ['full_name', 'email', 'company', 'focus_area', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Jane Smith'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@company.com'}),
            'company': forms.TextInput(attrs={'placeholder': 'Your Company'}),
            'focus_area': forms.Select(choices=[
                ('', 'Select assessment type'),
                ('marketing', 'Digital Marketing'),
                ('product', 'Product Management'),
                ('behavioral', 'Behavioral Assessment'),
                ('multiple', 'Multiple Assessments'),
                ('other', 'Not sure / Other'),
            ]),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Tell us about your hiring needs (optional)'
            }),
        }
        labels = {
            'full_name': 'Full Name',
            'email': 'Work Email',
            'company': 'Company Name',
            'focus_area': 'Assessment Interest',
            'notes': 'Additional Notes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make company field required for demo requests
        self.fields['company'].required = False
        self.fields['focus_area'].required = False
        self.fields['notes'].required = False
