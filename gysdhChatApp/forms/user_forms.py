from django import forms
from ..models import User, UserGroup

class UserGroupForm(forms.ModelForm):
    class Meta:
        model = UserGroup
        fields = ['name', 'description']
        labels = {
            'name': '组名',
            'description': '描述'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3})
        }

class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'companyCode', 'email', 'group', 'can_publish_announcements', 
                 'can_private_message', 'is_event_staff']
        labels = {
            'name': '姓名',
            'companyCode': '公司代码',
            'email': '邮箱',
            'group': '用户组',
            'can_publish_announcements': '允许发布公告',
            'can_private_message': '允许发送私信',
            'is_event_staff': '是否为工作人员'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'companyCode': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'can_publish_announcements': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'can_private_message': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_event_staff': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('name', 'companyCode', 'email', 'group', 'is_admin', 'can_publish_announcements', 
                 'can_private_message', 'is_event_staff')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 更新表单字段的样式
        self.fields['name'].widget.attrs.update({'class': 'form-input'})
        self.fields['companyCode'].widget.attrs.update({'class': 'form-input'})
        self.fields['email'].widget.attrs.update({'class': 'form-input'})
        self.fields['group'].widget.attrs.update({'class': 'form-select'})
        self.fields['is_admin'].widget.attrs.update({'class': 'form-checkbox'})
        self.fields['can_publish_announcements'].widget.attrs.update({'class': 'form-checkbox'})
        self.fields['can_private_message'].widget.attrs.update({'class': 'form-checkbox'})
        self.fields['is_event_staff'].widget.attrs.update({'class': 'form-checkbox'})
        
        # 添加字段标签
        self.fields['name'].label = '姓名'
        self.fields['companyCode'].label = '公司代码'
        self.fields['email'].label = '邮箱'
        self.fields['group'].label = '用户组'
        self.fields['is_admin'].label = '管理员权限'
        self.fields['can_publish_announcements'].label = '允许发布公告'
        self.fields['can_private_message'].label = '允许发送私信'
        self.fields['is_event_staff'].label = '是否为工作人员'
