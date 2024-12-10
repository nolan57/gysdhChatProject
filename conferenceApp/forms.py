from django import forms
from django.forms import inlineformset_factory
from .models.conference import Conference
from .models.contact import Contact
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, Submit, Div, HTML, Fieldset

class ContactForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-4 mb-0'),
                Column('title', css_class='form-group col-md-4 mb-0'),
                Column('phone', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-8 mb-0'),
                Column('is_primary', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('description', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            )
        )

    class Meta:
        model = Contact
        fields = ['name', 'title', 'phone', 'email', 'description', 'is_primary']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'rows': 3
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-indigo-600 dark:bg-gray-700 dark:border-gray-600'
            }),
        }

class ConferenceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                # 左列
                Div(
                    # 基本信息区域
                    Fieldset(
                        '基本信息',
                        Row(
                            Column('name', css_class='form-group col-md-12 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('code', css_class='form-group col-md-6 mb-0'),
                            Column('organizer', css_class='form-group col-md-6 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('description', css_class='form-group col-md-12 mb-0'),
                            css_class='form-row'
                        ),
                        css_class='mb-6'
                    ),
                    # 时间设置区域
                    Fieldset(
                        '时间设置',
                        Row(
                            Column('start_date', css_class='form-group col-md-6 mb-0'),
                            Column('end_date', css_class='form-group col-md-6 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('registration_start', css_class='form-group col-md-6 mb-0'),
                            Column('registration_end', css_class='form-group col-md-6 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('check_in_start', css_class='form-group col-md-6 mb-0'),
                            Column('check_in_end', css_class='form-group col-md-6 mb-0'),
                            css_class='form-row'
                        ),
                        css_class='mb-6'
                    ),
                    css_class='w-1/2 pr-4'
                ),
                # 右列
                Div(
                    # 场地信息区域
                    Fieldset(
                        '场地信息',
                        Row(
                            Column('venue_name', css_class='form-group col-md-12 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('venue_address', css_class='form-group col-md-12 mb-0'),
                            css_class='form-row'
                        ),
                        css_class='mb-6'
                    ),
                    # 参会人数设置区域
                    Fieldset(
                        '参会人数设置',
                        Row(
                            Column('min_participants', css_class='form-group col-md-6 mb-0'),
                            Column('max_participants', css_class='form-group col-md-6 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('company_min_participants', css_class='form-group col-md-6 mb-0'),
                            Column('company_max_participants', css_class='form-group col-md-6 mb-0'),
                            css_class='form-row'
                        ),
                        css_class='mb-6'
                    ),
                    # 其他设置区域
                    Fieldset(
                        '其他设置',
                        Row(
                            Column('status', css_class='form-group col-md-12 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('is_public', css_class='form-group col-md-6 mb-0'),
                            Column('require_approval', css_class='form-group col-md-6 mb-0'),
                            css_class='form-row'
                        ),
                        Row(
                            Column('additional_info', css_class='form-group col-md-12 mb-0'),
                            css_class='form-row'
                        ),
                        css_class='mb-6'
                    ),
                    css_class='w-1/2 pl-4'
                ),
                css_class='flex flex-wrap -mx-4'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_start = cleaned_data.get('registration_start')
        registration_end = cleaned_data.get('registration_end')
        check_in_start = cleaned_data.get('check_in_start')
        check_in_end = cleaned_data.get('check_in_end')
        min_participants = cleaned_data.get('min_participants')
        max_participants = cleaned_data.get('max_participants')
        company_min_participants = cleaned_data.get('company_min_participants')
        company_max_participants = cleaned_data.get('company_max_participants')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('会议开始时间不能晚于结束时间')

        if registration_start and registration_end and registration_start > registration_end:
            raise forms.ValidationError('报名开始时间不能晚于报名结束时间')

        if check_in_start and check_in_end and check_in_start > check_in_end:
            raise forms.ValidationError('签到开始时间不能晚于签到结束时间')

        if min_participants and max_participants and min_participants > max_participants:
            raise forms.ValidationError('最小参会人数不能大于最大参会人数')

        if company_min_participants and company_max_participants and company_min_participants > company_max_participants:
            raise forms.ValidationError('单位最小参会人数不能大于最大参会人数')

        return cleaned_data

    class Meta:
        model = Conference
        fields = '__all__'
        exclude = ['created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '请输入会议名称'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '请输入会议代码'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'rows': 3,
                'placeholder': '请输入会议描述'
            }),
            'organizer': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '请输入主办方'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'type': 'datetime-local'
            }),
            'registration_start': forms.DateTimeInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'type': 'datetime-local'
            }),
            'registration_end': forms.DateTimeInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'type': 'datetime-local'
            }),
            'check_in_start': forms.DateTimeInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'type': 'datetime-local'
            }),
            'check_in_end': forms.DateTimeInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'type': 'datetime-local'
            }),
            'venue_name': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '请输入场地名称'
            }),
            'venue_address': forms.TextInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '请输入场地地址'
            }),
            'min_participants': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '最小参会人数'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '最大参会人数'
            }),
            'company_min_participants': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '单位最小参会人数'
            }),
            'company_max_participants': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'placeholder': '单位最大参会人数'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-indigo-600 dark:bg-gray-700 dark:border-gray-600'
            }),
            'require_approval': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-indigo-600 dark:bg-gray-700 dark:border-gray-600'
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-textarea rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100',
                'rows': 3,
                'placeholder': '其他补充信息'
            }),
        }

ContactFormSet = inlineformset_factory(
    Conference, Contact, form=ContactForm,
    extra=1, can_delete=False
)
