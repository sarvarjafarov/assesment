from django import forms

from clients.models import ClientAccount, ClientProject
from .models import HiringPipeline


class HiringPipelineForm(forms.ModelForm):
    required_skills_text = forms.CharField(
        label='Required Skills',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Enter skills separated by commas, e.g. Python, Django, REST APIs',
        }),
        help_text='Comma-separated list of required skills.',
    )
    preferred_skills_text = forms.CharField(
        label='Preferred Skills',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Enter nice-to-have skills separated by commas',
        }),
        help_text='Comma-separated list of preferred (nice-to-have) skills.',
    )

    class Meta:
        model = HiringPipeline
        fields = [
            'title', 'job_description', 'experience_range',
            'seniority_level', 'assessment_types', 'automation_mode',
            'screening_threshold', 'passing_score', 'max_candidates',
            'project',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Senior Frontend Engineer Pipeline'}),
            'job_description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Paste the full job description here...'}),
            'experience_range': forms.TextInput(attrs={'placeholder': 'e.g. 3-5 years'}),
            'screening_threshold': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'passing_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'max_candidates': forms.NumberInput(attrs={'min': 1, 'max': 500}),
        }

    def __init__(self, *args, client: ClientAccount = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client

        # Limit project choices to this client's projects
        if client:
            self.fields['project'].queryset = ClientProject.objects.filter(
                client=client
            ).exclude(status=ClientProject.STATUS_ARCHIVED)
        self.fields['project'].required = False

        # Build assessment type choices from client's allowed assessments
        assessment_choices = [
            (code, meta['label'])
            for code, meta in ClientAccount.ASSESSMENT_DETAILS.items()
        ]
        self.fields['assessment_types'] = forms.MultipleChoiceField(
            choices=assessment_choices,
            widget=forms.CheckboxSelectMultiple,
            required=True,
            help_text='Select which assessments to send to shortlisted candidates.',
        )

        # Populate skills text from JSON on edit
        if self.instance and self.instance.pk:
            self.fields['required_skills_text'].initial = ', '.join(
                self.instance.required_skills or []
            )
            self.fields['preferred_skills_text'].initial = ', '.join(
                self.instance.preferred_skills or []
            )

    def clean_required_skills_text(self):
        text = self.cleaned_data.get('required_skills_text', '')
        return [s.strip() for s in text.split(',') if s.strip()]

    def clean_preferred_skills_text(self):
        text = self.cleaned_data.get('preferred_skills_text', '')
        return [s.strip() for s in text.split(',') if s.strip()]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.client = self.client
        instance.required_skills = self.cleaned_data['required_skills_text']
        instance.preferred_skills = self.cleaned_data['preferred_skills_text']
        if commit:
            instance.save()
        return instance


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ResumeUploadForm(forms.Form):
    MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB

    resumes = forms.FileField(
        label='Upload Resumes',
        help_text='Accepted formats: PDF, DOCX (max 10 MB each). You can select multiple files.',
        widget=MultipleFileInput(attrs={
            'accept': '.pdf,.docx',
        }),
    )

    def clean_resumes(self):
        files = self.files.getlist('resumes')
        for f in files:
            if f.size > self.MAX_RESUME_SIZE:
                raise forms.ValidationError(
                    f'File "{f.name}" exceeds the 10 MB size limit.'
                )
            name = f.name.lower()
            if not (name.endswith('.pdf') or name.endswith('.docx')):
                raise forms.ValidationError(
                    f'File "{f.name}" is not a PDF or DOCX file.'
                )
        return files


class CandidateReviewForm(forms.Form):
    DECISION_CHOICES = [
        ('advance', 'Advance'),
        ('hold', 'Hold'),
        ('reject', 'Reject'),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional notes...'}),
    )
