# DDL管家
import json
import os
from datetime import datetime
from colorama import init, Fore, Back, Style

# 初始化colorama
init(autoreset=True)

# 数据文件路径
DATA_FILE = "tasks.json"

"""  数据结构：
tasks: [{}, {}, {}, ...]
{
    "course": "高等数学",                # 课程名称，字符串
    "ddl": "2025-06-20 23:59",          # 截止时间，字符串（格式固定）
    "description": "第三章课后题",       # 作业描述，字符串（可选）
    "created_at": "2025-03-15 20:30:00", # 创建时间，字符串，自动生成
    "completed": False                   # 是否完成，布尔值
}
"""

# ==============================数据操作==============================
def load_tasks():
    """加载已有任务（如果文件存在）"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    """保存任务到文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


# ===============================工具函数===============================
def validate_datetime(datetime_str):
    """校验日期时间字符串格式是否为 YYYY-MM-DD HH:MM，成功返回 datetime 对象，失败返回 None"""
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

def days_until(ddl_str):
    """计算距离截止日期还有几天，返回整数（负数表示已过期）"""
    try:
        ddl = datetime.strptime(ddl_str, "%Y-%m-%d %H:%M")
        now = datetime.now()
        delta = ddl - now
        return delta.days
    except:
        return None  # 日期格式错误时返回 None


# ===============================任务操作===============================
def add_task(tasks):
    """添加一项作业"""
    print("\n--- 添加新作业 ---")
    course = input("课程名称: ").strip()
    ddl_str = input("截止时间 (格式: YYYY-MM-DD HH:MM, 例如 2025-12-31 23:59): ").strip()

    # 简单校验日期格式
    if validate_datetime(ddl_str) is None:
        print("❌ 日期格式错误，请按格式输入！")
        return tasks

    description = input("作业描述 (可选): ").strip()

    # 创建任务字典
    task = {
        "course": course,
        "ddl": ddl_str,
        "description": description,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "completed": False
    }

    tasks.append(task)
    save_tasks(tasks)  # 立即保存到文件
    print(f"✅ 已添加作业：{course} - {ddl_str}")
    return tasks

def show_tasks(tasks):
    """显示当前剩余作业"""
    print("\n--- 当前所有作业 ---")
    if not tasks:
        print("暂无作业，快去添加吧！")
    else:
        # 按截止时间排序（越紧急越靠前）
        sorted_tasks = sorted(tasks, key=lambda t: t['ddl'])

        for i, task in enumerate(sorted_tasks, 1):  # task[i]
            # 计算剩余天数
            days = days_until(task['ddl'])

            # 根据剩余天数决定颜色和状态符号
            if task.get('completed'):
                status = "✅"
                color = Fore.GREEN
            elif days is None:
                status = "❓"
                color = Fore.YELLOW
            elif days < 0:
                status = "⏰"  # 已过期
                color = Fore.RED + Back.YELLOW  # 红字黄底，更醒目
            elif days <= 3:
                status = "🔥"
                color = Fore.RED
            elif days <= 7:
                status = "⚠️"
                color = Fore.YELLOW
            else:
                status = "📌"
                color = Fore.CYAN

            # 构建显示文本
            line = (f"{i}. {status} {color}{task['course']}{Style.RESET_ALL} "
                    f"- 截止: {task['ddl']}")
            if days is not None:
                if days >= 0:
                    line += f" (剩余 {days} 天)"
                else:
                    line += f" (已过期 {-days} 天)"

            print(line)

            if task['description']:
                print(f"   备注: {task['description']}")

    # 在底部增加统计信息
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get('completed'))
    expired = sum(1 for t in tasks if
                  not t.get('completed') and days_until(t['ddl']) is not None and days_until(t['ddl']) < 0)
    urgent = sum(1 for t in tasks if
                 not t.get('completed') and days_until(t['ddl']) is not None and 0 <= days_until(t['ddl']) <= 3)

    print("\n" + "-" * 30)
    print(f"📊 总计: {total} 项作业")
    print(f"✅ 已完成: {completed}")
    print(f"⏰ 已过期: {expired}")
    print(f"🔥 紧急(≤3天): {urgent}")

    input("\n按 Enter 键继续...")
    return tasks

def mark_completed(tasks):
    """标记某个作业为已完成"""
    # 处理无作业情况
    if not tasks:
        print("暂无作业可标记")
        input("\n按 Enter 键继续...")
        return tasks

    # 先展示一遍作业，让用户选择序号
    print("\n--- 选择要标记完成的作业 ---")
    for i, task in enumerate(tasks, 1):
        status = "✅" if task.get('completed') else "⏳"
        print(f"{i}. {status} {task['course']} - 截止: {task['ddl']}")

    try:
        idx = int(input("请输入要标记的作业编号: ")) - 1
        if 0 <= idx < len(tasks):
            if tasks[idx].get('completed'):
                print(f"作业 '{tasks[idx]['course']}' 已经是完成状态")
            else:
                tasks[idx]['completed'] = True
                save_tasks(tasks)
                print(f"✅ 已标记完成: {tasks[idx]['course']}")
        else:
            print("❌ 编号超出范围")
    except ValueError:
        print("❌ 请输入有效数字")

    input("\n按 Enter 键继续...")
    return tasks

def delete_task(tasks):
    """删除指定的作业"""
    if not tasks:
        print("暂无作业可删除")
        input("\n按 Enter 键继续...")
        return tasks

    print("\n--- 选择要删除的作业 ---")
    # 显示所有作业（带编号、状态、课程、截止时间）
    for i, task in enumerate(tasks, 1):
        status = "✅" if task.get('completed') else "⏳"
        # 简单显示，不需要颜色，以免干扰
        print(f"{i}. {status} {task['course']} - 截止: {task['ddl']}")

    try:
        idx = int(input("请输入要删除的作业编号: ")) - 1
        if 0 <= idx < len(tasks):
            # 二次确认，防止误删
            confirm = input(f"确定要删除 '{tasks[idx]['course']}' 吗？(y/n): ").strip().lower()
            if confirm == 'y' or confirm == 'yes':
                deleted = tasks.pop(idx)
                save_tasks(tasks)
                print(f"🗑️ 已删除作业: {deleted['course']}")
            else:
                print("取消删除")
        else:
            print("❌ 编号超出范围")
    except ValueError:
        print("❌ 请输入有效数字")

    input("\n按 Enter 键继续...")
    return tasks


# ===============================主程序入口==============================
def main():
    tasks = load_tasks()  # 启动时加载已有任务
    print("=" * 30)
    print("    西电 DDL 管家")
    print("=" * 30)

    while True:
        print("\n请选择操作：")
        print("1. 添加作业")
        print("2. 查看所有作业")
        print("3. 标记作业完成")
        print("4. 删除作业")
        print("5. 退出")

        choice = input("请输入数字(1-5): ").strip()

        # list为可变对象，传入实参的引用，可不重新赋值
        # 若函数内重新为list赋值，才需使用赋值形式修改
        if choice == "1":
            tasks = add_task(tasks)
        elif choice == "2":
            tasks = show_tasks(tasks)
        elif choice == "3":
            tasks = mark_completed(tasks)
        elif choice == "4":
            tasks = delete_task(tasks)
        elif choice == "5":
            print("感谢使用，再见！")
            break

        else:
            print("❌ 无效输入，请输入1-3之间的数字")


if __name__ == "__main__":
    main()
