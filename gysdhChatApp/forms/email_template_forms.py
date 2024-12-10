from django import forms
from ..models import EmailTemplate
import json

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'content', 'description', 'variables']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'variables': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_variables(self):
        variables = self.cleaned_data.get('variables')
        if not variables:
            return {}
        
        # 如果variables已经是字典，直接返回
        if isinstance(variables, dict):
            return variables
            
        # 如果是字符串，尝试解析JSON
        try:
            return json.loads(variables)
        except json.JSONDecodeError:
            raise forms.ValidationError('变量必须是有效的JSON格式')
        except Exception as e:
            raise forms.ValidationError(f'变量验证失败：{str(e)}')
