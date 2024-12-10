from django.core.management.base import BaseCommand
import pandas as pd
import os

class Command(BaseCommand):
    help = '创建用户导入Excel模板文件'

    def handle(self, *args, **options):
        # 模板数据
        data = {
            'name': ['张三', '李四'],  # 示例姓名
            'companyCode': ['COMP001', 'COMP002'],  # 示例公司代码
            'email': ['zhangsan@example.com', 'lisi@example.com'],  # 示例邮箱
            'is_admin': ['F', 'F']  # 是否管理员，默认为F（否）
        }
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 确保目标目录存在
        template_dir = os.path.join('gysdhChatApp', 'static', 'templates')
        os.makedirs(template_dir, exist_ok=True)
        
        # 保存为Excel文件
        template_path = os.path.join(template_dir, 'user_import_template.xlsx')
        df.to_excel(template_path, index=False)
        
        self.stdout.write(self.style.SUCCESS(f'成功创建模板文件：{template_path}'))
