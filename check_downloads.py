from gysdhChatApp.models import FileDownloadLog, User

print("=== 检查文件下载记录 ===")
logs = FileDownloadLog.objects.select_related('user').all()
for log in logs:
    print(f"\n下载记录 ID: {log.id}")
    print(f"文件名: {log.file_name}")
    print(f"用户ID: {log.user_id}")
    if log.user:
        print(f"用户信息: ID={log.user.id}, 名字={log.user.name}, 编号={log.user.number}")
    else:
        print("用户不存在")
    print("-" * 50)

print("\n=== 检查用户记录 ===")
users = User.objects.all()
for user in users:
    print(f"\n用户 ID: {user.id}")
    print(f"名字: {user.name}")
    print(f"编号: {user.number}")
    print("-" * 50)
