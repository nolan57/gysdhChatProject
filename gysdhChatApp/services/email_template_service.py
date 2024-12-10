from django.template import Template, Context
from ..models import EmailTemplate

class EmailTemplateService:
    @staticmethod
    def render_template(template_name: str, context_data: dict) -> tuple[str, str]:
        """
        渲染邮件模板
        :param template_name: 模板名称
        :param context_data: 模板变量数据
        :return: 渲染后的主题和内容
        """
        try:
            template = EmailTemplate.objects.get(name=template_name)
            
            # 渲染主题
            subject_template = Template(template.subject)
            subject = subject_template.render(Context(context_data))
            
            # 渲染内容
            content_template = Template(template.content)
            content = content_template.render(Context(context_data))
            
            return subject, content
        except EmailTemplate.DoesNotExist:
            raise ValueError(f"Template '{template_name}' does not exist")
        except KeyError as e:
            raise ValueError(f"Missing required variable: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error rendering template: {str(e)}")

    @staticmethod
    def get_template_variables(template_name: str) -> dict:
        """
        获取模板的可用变量
        :param template_name: 模板名称
        :return: 变量字典
        """
        try:
            template = EmailTemplate.objects.get(name=template_name)
            return template.variables
        except EmailTemplate.DoesNotExist:
            raise ValueError(f"Template '{template_name}' does not exist")
