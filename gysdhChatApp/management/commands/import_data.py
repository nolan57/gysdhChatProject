import pandas as pd
from django.core.management.base import BaseCommand
from gysdhChatApp.models import User  # 替换成你的模型

class Command(BaseCommand):
    help = 'Import data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str)

    def handle(self, *args, **kwargs):
        excel_file = kwargs['excel_file']
        df = pd.read_excel(excel_file)

        for index, row in df.iterrows():
            # 假设你的模型有字段 'field1', 'field2', 'field3'
            User.objects.create(
                number=row['id'],  # 替换成你的列名
                name=row['姓名'],
                companyCode=row['供应商代码'],
            )

        self.stdout.write(self.style.SUCCESS('Data imported successfully!'))
