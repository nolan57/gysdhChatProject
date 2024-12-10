from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import datetime

# Create your models here.

class Conference(models.Model):
    """会议模型"""
    title = models.CharField(max_length=200, verbose_name='会议标题')
    description = models.TextField(verbose_name='会议描述')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    location = models.CharField(max_length=200, verbose_name='会议地点')
    capacity = models.IntegerField(verbose_name='容纳人数')
    registration_form = models.OneToOneField(
        'RegistrationForm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conference',
        verbose_name='报名表单'
    )

    class Meta:
        verbose_name = '会议'
        verbose_name_plural = '会议'

    def __str__(self):
        return self.title

class RegistrationForm(models.Model):
    """报名表单模型"""
    name = models.CharField(max_length=200, verbose_name='表单名称')
    description = models.TextField(blank=True, verbose_name='表单描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_formio = models.BooleanField(default=False, verbose_name='是否为Form.io表单')
    formio_schema = models.JSONField(null=True, blank=True, verbose_name='Form.io表单配置')
    formio_logic_rules = models.JSONField(null=True, blank=True, verbose_name='Form.io逻辑规则',
        help_text='存储Form.io表单的条件逻辑规则,格式为:[{"triggerField":"field1","operator":"equals",...}]')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '报名表单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def validate_formio_data(self, data):
        """验证 Form.io 提交的数据"""
        if not self.is_formio:
            raise ValidationError('此表单不是 Form.io 表单')
            
        if not isinstance(data, dict):
            raise ValidationError('表单数据格式不正确')
        
        # 获取表单 schema
        if not self.formio_schema:
            raise ValidationError('表单配置不存在')
        
        # 验证必填字段
        components = self.formio_schema.get('components', [])
        for component in components:
            if component.get('validate', {}).get('required', False):
                key = component.get('key')
                if not key or not data.get(key):
                    raise ValidationError(f'字段 {component.get("label", key)} 为必填项')
        
        # 验证字段类型和格式
        self._validate_field_types(components, data)
    
    def _validate_field_types(self, components, data):
        """验证字段类型和格式"""
        for component in components:
            key = component.get('key')
            if not key or key not in data:
                continue
            
            value = data[key]
            component_type = component.get('type')
            
            # 验证数字类型
            if component_type == 'number':
                try:
                    float(value)
                except (TypeError, ValueError):
                    raise ValidationError(f'字段 {component.get("label", key)} 必须是数字')
            
            # 验证日期类型
            elif component_type == 'datetime':
                try:
                    datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
                except (TypeError, ValueError):
                    raise ValidationError(f'字段 {component.get("label", key)} 必须是有效的日期时间')
            
            # 验证选项类型
            elif component_type in ['select', 'radio']:
                values = component.get('data', {}).get('values', [])
                valid_values = [item.get('value') for item in values]
                if value not in valid_values:
                    raise ValidationError(f'字段 {component.get("label", key)} 的值不在有效选项中')
            
            # 验证多选类型
            elif component_type == 'checkbox':
                if not isinstance(value, (list, bool)):
                    raise ValidationError(f'字段 {component.get("label", key)} 的值格式不正确')
                if isinstance(value, list):
                    values = component.get('data', {}).get('values', [])
                    valid_values = [item.get('value') for item in values]
                    for v in value:
                        if v not in valid_values:
                            raise ValidationError(f'字段 {component.get("label", key)} 的值不在有效选项中')

    def apply_formio_logic_rules(self, data):
        """应用Form.io表单逻辑规则"""
        if not self.formio_logic_rules:
            return data

        modified_data = data.copy()
        for rule in self.formio_logic_rules:
            trigger_field = rule.get('triggerField')
            operator = rule.get('operator')
            value = rule.get('value')
            target_field = rule.get('targetField')
            action = rule.get('action')

            if not all([trigger_field, operator, target_field, action]):
                continue

            # 检查触发条件是否满足
            trigger_value = data.get(trigger_field)
            if self._evaluate_condition(trigger_value, operator, value):
                # 应用动作
                modified_data = self._apply_action(modified_data, target_field, action)

        return modified_data

    def _evaluate_condition(self, field_value, operator, test_value):
        """评估条件是否满足"""
        if operator == 'equals':
            return field_value == test_value
        elif operator == 'not_equals':
            return field_value != test_value
        elif operator == 'contains':
            return test_value in str(field_value)
        elif operator == 'not_contains':
            return test_value not in str(field_value)
        elif operator == 'greater_than':
            try:
                return float(field_value) > float(test_value)
            except (ValueError, TypeError):
                return False
        elif operator == 'less_than':
            try:
                return float(field_value) < float(test_value)
            except (ValueError, TypeError):
                return False
        elif operator == 'is_empty':
            return not field_value
        elif operator == 'is_not_empty':
            return bool(field_value)
        return False

    def _apply_action(self, data, target_field, action):
        """应用动作到目标字段"""
        if action == 'clear_value':
            data[target_field] = None
        elif action == 'set_value' and 'value' in action:
            data[target_field] = action['value']
        return data

    def save_formio_submission(self, user, company, data):
        """保存 Form.io 表单提交"""
        # 验证表单数据
        self.validate_formio_data(data)
        
        # 应用表单逻辑规则
        if self.formio_schema and 'logic_rules' in self.formio_schema:
            data = self._apply_formio_logic_rules(data)
        
        # 验证用户和公司状态
        if not user.is_active:
            raise ValidationError('用户账号已禁用')
        if not company or not company.is_active:
            raise ValidationError('公司账号已禁用')
        
        # 验证会议状态
        conference = self.conference
        if not conference:
            raise ValidationError('表单未关联会议')
        if not conference.is_registration_open():
            raise ValidationError('当前不在报名时间内')
            
        # 检查是否已提交
        if FormioSubmission.objects.filter(
            conference=conference,
            user=user
        ).exists():
            raise ValidationError('您已经提交过此会议的报名表单')
        
        # 保存提交记录
        submission = FormioSubmission.objects.create(
            conference=conference,
            form=self,
            user=user,
            company=company,
            data=data
        )
        
        return submission

    def _apply_formio_logic_rules(self, data):
        """应用表单逻辑规则"""
        if not isinstance(data, dict):
            return data

        modified_data = data.copy()
        logic_rules = self.formio_schema.get('logic_rules', [])

        for rule in logic_rules:
            trigger = rule.get('trigger', {})
            action = rule.get('action', {})

            # 获取规则配置
            trigger_field = trigger.get('field')
            operator = trigger.get('operator')
            test_value = trigger.get('value')
            target_field = action.get('field')
            action_type = action.get('type')
            action_value = action.get('value')

            if not all([trigger_field, operator, target_field, action_type]):
                continue

            # 检查触发条件
            field_value = data.get(trigger_field)
            if self._evaluate_logic_condition(field_value, operator, test_value):
                # 应用动作
                modified_data = self._apply_logic_action(
                    modified_data, 
                    target_field, 
                    action_type,
                    action_value
                )

        return modified_data

    def _evaluate_logic_condition(self, field_value, operator, test_value):
        """评估逻辑条件"""
        if operator == 'eq':
            return field_value == test_value
        elif operator == 'neq':
            return field_value != test_value
        elif operator == 'contains':
            return str(test_value).lower() in str(field_value).lower()
        elif operator == 'notContains':
            return str(test_value).lower() not in str(field_value).lower()
        elif operator == 'gt':
            try:
                return float(field_value) > float(test_value)
            except (ValueError, TypeError):
                return False
        elif operator == 'lt':
            try:
                return float(field_value) < float(test_value)
            except (ValueError, TypeError):
                return False
        elif operator == 'empty':
            return not field_value
        elif operator == 'notEmpty':
            return bool(field_value)
        return False

    def _apply_logic_action(self, data, target_field, action_type, action_value=None):
        """应用逻辑动作"""
        if action_type == 'clear':
            data[target_field] = None
        elif action_type == 'setValue' and action_value is not None:
            data[target_field] = action_value
        elif action_type == 'require':
            # 在验证阶段处理必填项
            if target_field not in data or not data[target_field]:
                raise ValidationError(f'字段 {target_field} 为必填项')
        return data

class FormField(models.Model):
    """表单字段模型"""
    FIELD_TYPES = (
        ('text', '单行文本'),
        ('textarea', '多行文本'),
        ('number', '数字'),
        ('select', '下拉选择'),
        ('radio', '单选'),
        ('checkbox', '多选'),
        ('date', '日期'),
        ('time', '时间'),
        ('file', '文件上传')
    )

    form = models.ForeignKey(
        RegistrationForm,
        on_delete=models.CASCADE,
        related_name='fields',
        verbose_name='所属表单'
    )
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, verbose_name='字段类型')
    label = models.CharField(max_length=100, verbose_name='字段标签')
    name = models.CharField(max_length=100, verbose_name='字段名称')
    placeholder = models.CharField(max_length=200, blank=True, verbose_name='占位文本')
    help_text = models.CharField(max_length=200, blank=True, verbose_name='帮助文本')
    required = models.BooleanField(default=True, verbose_name='是否必填')
    order = models.IntegerField(default=0, verbose_name='排序')
    validation_regex = models.CharField(max_length=200, blank=True, verbose_name='验证正则表达式')
    error_message = models.CharField(max_length=200, blank=True, verbose_name='错误提示')
    default_value = models.CharField(max_length=200, blank=True, verbose_name='默认值')
    is_unique_in_company = models.BooleanField(default=False, verbose_name='公司内唯一')
    max_occurrences = models.IntegerField(null=True, blank=True, verbose_name='最大出现次数')

    class Meta:
        verbose_name = '表单字段'
        verbose_name_plural = '表单字段'
        ordering = ['order']

    def __str__(self):
        return f"{self.form.name} - {self.label}"

class FieldOption(models.Model):
    """字段选项模型"""
    field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='所属字段'
    )
    label = models.CharField(max_length=100, verbose_name='选项标签')
    value = models.CharField(max_length=100, verbose_name='选项值')
    order = models.IntegerField(default=0, verbose_name='排序')
    is_exclusive = models.BooleanField(default=False, verbose_name='是否互斥')
    max_selections = models.IntegerField(null=True, blank=True, verbose_name='最大选择数')

    class Meta:
        verbose_name = '字段选项'
        verbose_name_plural = '字段选项'
        ordering = ['order']

    def __str__(self):
        return f"{self.field.label} - {self.label}"

class FieldLogicRule(models.Model):
    """字段逻辑规则模型"""
    OPERATORS = (
        ('equals', '等于'),
        ('not_equals', '不等于'),
        ('contains', '包含'),
        ('not_contains', '不包含'),
        ('greater_than', '大于'),
        ('less_than', '小于'),
        ('in', '在列表中'),
        ('not_in', '不在列表中'),
        ('starts_with', '开头是'),
        ('ends_with', '结尾是'),
        ('is_empty', '为空'),
        ('is_not_empty', '不为空'),
        ('between', '在范围内')
    )

    ACTIONS = (
        ('show', '显示'),
        ('hide', '隐藏'),
        ('enable', '启用'),
        ('disable', '禁用'),
        ('require', '必填'),
        ('unrequire', '非必填'),
        ('set_value', '设置值'),
        ('clear_value', '清除值')
    )

    source_field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
        related_name='logic_rules',
        verbose_name='源字段'
    )
    target_field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
        related_name='dependent_rules',
        verbose_name='目标字段'
    )
    operator = models.CharField(max_length=20, choices=OPERATORS, verbose_name='操作符')
    value = models.CharField(max_length=200, blank=True, verbose_name='比较值')
    action = models.CharField(max_length=20, choices=ACTIONS, verbose_name='动作')
    action_value = models.CharField(max_length=200, blank=True, verbose_name='动作值')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '字段逻辑规则'
        verbose_name_plural = '字段逻辑规则'
        constraints = [
            models.UniqueConstraint(
                fields=['source_field', 'target_field', 'operator', 'value', 'action'],
                name='unique_field_logic_rule'
            )
        ]

    def __str__(self):
        return f"{self.source_field.label} -> {self.target_field.label}"

    def clean(self):
        """验证规则的有效性"""
        if self.source_field.form != self.target_field.form:
            raise ValidationError('源字段和目标字段必须属于同一个表单')

        # 验证操作符和值的匹配
        if self.operator in ['greater_than', 'less_than']:
            try:
                float(self.value)
            except ValueError:
                raise ValidationError('数值比较操作符需要数字类型的值')

        if self.operator == 'between':
            try:
                min_val, max_val = self.value.split(',')
                float(min_val.strip())
                float(max_val.strip())
            except (ValueError, AttributeError):
                raise ValidationError('范围值格式应为"最小值,最大值"，例如："0,100"')

        if self.operator in ['in', 'not_in']:
            if not self.value.strip():
                raise ValidationError('列表操作符需要非空的值列表')

        # 验证动作和值的匹配
        if self.action == 'set_value' and not self.action_value:
            raise ValidationError('设置值动作需要指定具体的值')

        # 验证字段类型的兼容性
        if self.action == 'set_value':
            if self.target_field.field_type == 'number':
                try:
                    float(self.action_value)
                except ValueError:
                    raise ValidationError('数字类型字段只能设置数字值')
            elif self.target_field.field_type in ['select', 'radio', 'checkbox']:
                valid_values = set(opt.value for opt in self.target_field.options.all())
                if self.action_value not in valid_values:
                    raise ValidationError('设置的值必须是选项中的有效值')

    def validate_conflicts(self):
        """检查规则冲突"""
        conflicting_rules = FieldLogicRule.objects.filter(
            source_field=self.source_field,
            target_field=self.target_field
        ).exclude(id=self.id)

        for rule in conflicting_rules:
            # 检查相反的动作
            if (
                (self.action == 'show' and rule.action == 'hide') or
                (self.action == 'hide' and rule.action == 'show') or
                (self.action == 'enable' and rule.action == 'disable') or
                (self.action == 'disable' and rule.action == 'enable') or
                (self.action == 'require' and rule.action == 'unrequire') or
                (self.action == 'unrequire' and rule.action == 'require')
            ):
                # 检查条件是否可能同时成立
                if self._conditions_may_conflict(rule):
                    raise ValidationError(
                        f'当前规则与已存在的规则"{rule}"可能产生冲突'
                    )

    def _conditions_may_conflict(self, other_rule):
        """检查两个规则的条件是否可能同时成立"""
        # 相同操作符，相同值
        if self.operator == other_rule.operator and self.value == other_rule.value:
            return True

        # 互补操作符
        if (
            (self.operator == 'equals' and other_rule.operator == 'not_equals') or
            (self.operator == 'not_equals' and other_rule.operator == 'equals') or
            (self.operator == 'contains' and other_rule.operator == 'not_contains') or
            (self.operator == 'not_contains' and other_rule.operator == 'contains') or
            (self.operator == 'in' and other_rule.operator == 'not_in') or
            (self.operator == 'not_in' and other_rule.operator == 'in')
        ):
            return True

        # 数值比较可能重叠
        if self.operator in ['greater_than', 'less_than'] and other_rule.operator in ['greater_than', 'less_than']:
            try:
                val1 = float(self.value)
                val2 = float(other_rule.value)
                if (
                    (self.operator == 'greater_than' and other_rule.operator == 'less_than' and val1 < val2) or
                    (self.operator == 'less_than' and other_rule.operator == 'greater_than' and val1 > val2)
                ):
                    return True
            except ValueError:
                return False

        return False

    def save(self, *args, **kwargs):
        """保存前进行验证"""
        self.clean()
        self.validate_conflicts()
        super().save(*args, **kwargs)

class Company(models.Model):
    """公司模型"""
    name = models.CharField(max_length=200, verbose_name='公司名称')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        verbose_name = '公司'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class FormioSubmission(models.Model):
    """Form.io 表单提交记录"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='formio_submissions')
    form = models.ForeignKey(RegistrationForm, on_delete=models.CASCADE, related_name='formio_submissions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='formio_submissions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='formio_submissions')
    data = models.JSONField(help_text='表单提交的数据')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待审核'),
            ('approved', '已通过'),
            ('rejected', '已拒绝')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Form.io 表单提交'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        # 每个用户在每个会议只能提交一次
        unique_together = [('conference', 'user')]
    
    def __str__(self):
        return f'{self.user.name} - {self.conference.name} - {self.created_at}'
    
    def clean(self):
        """验证表单提交"""
        # 验证会议状态
        if not self.conference.is_registration_open():
            raise ValidationError('当前不在报名时间内')
        
        # 验证表单类型
        if not self.form.is_formio:
            raise ValidationError('表单类型不正确')
        
        # 验证用户权限
        if not self.user.is_active:
            raise ValidationError('用户账号已禁用')
        
        # 验证公司信息
        if not self.company.is_active:
            raise ValidationError('公司账号已禁用')
        
        # 验证表单数据
        self.validate_form_data()
    
    def validate_form_data(self):
        """验证表单数据"""
        if not isinstance(self.data, dict):
            raise ValidationError('表单数据格式不正确')
        
        # 获取表单 schema
        schema = self.form.formio_schema
        if not schema:
            raise ValidationError('表单配置不存在')
        
        # 验证必填字段
        components = schema.get('components', [])
        for component in components:
            if component.get('validate', {}).get('required', False):
                key = component.get('key')
                if not key or not self.data.get(key):
                    raise ValidationError(f'字段 {component.get("label", key)} 为必填项')
        
        # 验证字段类型和格式
        self.validate_field_types(components)
    
    def validate_field_types(self, components):
        """验证字段类型和格式"""
        for component in components:
            key = component.get('key')
            if not key or key not in self.data:
                continue
            
            value = self.data[key]
            component_type = component.get('type')
            
            # 验证数字类型
            if component_type == 'number':
                try:
                    float(value)
                except (TypeError, ValueError):
                    raise ValidationError(f'字段 {component.get("label", key)} 必须是数字')
            
            # 验证日期类型
            elif component_type == 'datetime':
                try:
                    datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
                except (TypeError, ValueError):
                    raise ValidationError(f'字段 {component.get("label", key)} 必须是有效的日期时间')
            
            # 验证选项类型
            elif component_type in ['select', 'radio']:
                values = component.get('data', {}).get('values', [])
                valid_values = [item.get('value') for item in values]
                if value not in valid_values:
                    raise ValidationError(f'字段 {component.get("label", key)} 的值不在有效选项中')
            
            # 验证多选类型
            elif component_type == 'checkbox':
                if not isinstance(value, (list, bool)):
                    raise ValidationError(f'字段 {component.get("label", key)} 的值格式不正确')
                if isinstance(value, list):
                    values = component.get('data', {}).get('values', [])
                    valid_values = [item.get('value') for item in values]
                    for v in value:
                        if v not in valid_values:
                            raise ValidationError(f'字段 {component.get("label", key)} 的值不在有效选项中')
