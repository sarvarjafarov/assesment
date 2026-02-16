from django import forms
from .models import DemoRequest


class PositionApplyForm(forms.Form):
    full_name = forms.CharField(max_length=200, label="Full Name")
    email = forms.EmailField(label="Email Address")
    resume = forms.FileField(label="Resume", help_text="PDF or DOCX, max 5 MB")

    def clean_resume(self):
        f = self.cleaned_data.get("resume")
        if not f:
            return f
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Resume must be smaller than 5 MB.")
        allowed = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if getattr(f, "content_type", "") not in allowed:
            raise forms.ValidationError("Upload a PDF or DOCX file.")
        header = f.read(8)
        f.seek(0)
        if not (header.startswith(b"%PDF") or header.startswith(b"PK")):
            raise forms.ValidationError("Invalid file format.")
        return f

    def clean_email(self):
        return self.cleaned_data["email"].lower().strip()


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
