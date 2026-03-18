# DDL管家
import csv
import difflib
import json
import os
import shutil
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
    """加载文件，若文件损坏，则将备份保存到主文件"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            # 如果文件损坏，尝试从备份恢复
            backup_file = DATA_FILE.replace('.json', '_backup.json')
            if os.path.exists(backup_file):
                print("===========WARNING!===========")
                print("检测到主文件损坏，正在从备份恢复...")
                shutil.copy(backup_file, DATA_FILE)
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                return []
    return []

def save_tasks(tasks):
    """保存文件及文件备份"""
    # 先备份现有文件（如果存在）
    if os.path.exists(DATA_FILE):
        shutil.copy(DATA_FILE, DATA_FILE.replace('.json', '_backup.json'))
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

def filter_tasks_by_course(tasks, course_keyword):
    """根据课程关键词模糊匹配（包含+相似度）"""
    if not course_keyword:
        return tasks
    keyword = course_keyword.lower().strip()

    # 先尝试包含匹配（不区分大小写）
    exact_matches = [t for t in tasks if keyword in t['course'].lower()]
    if exact_matches:
        return exact_matches  # 有包含匹配就直接返回

    # 如果没有包含匹配，则计算相似度，找出相似度最高的课程
    # 获取所有课程名（去重）
    all_courses = list({t['course'] for t in tasks})
    # 获取最相似的几个课程名（cutoff 可调整相似度阈值）
    # 为避免因搜索不到而遗漏作业，cutoff值设置较低
    close_matches = difflib.get_close_matches(keyword, all_courses, n=len(all_courses), cutoff=0.1)

    if close_matches:
        print(f"您是不是想找：{', '.join(close_matches)}？将显示这些课程的作业")
        # 返回所有课程名在 close_matches 中的任务
        return [t for t in tasks if t['course'] in close_matches]
    else:
        return []  # 没找到匹配

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
    """显示作业，支持按课程筛选"""
    print("\n--- 查看作业 ---")

    display_tasks = tasks  # 默认显示所有作业
    # 无作业情况
    if not display_tasks:
        print("暂无作业")
        input("\n按 Enter 键继续...")
        return tasks

    # ==========按课程筛选==========
    filter_choice = input("是否按课程筛选？(y/n，默认n): ").strip().lower()
    if filter_choice == 'y' or filter_choice == 'yes':
        course_keyword = input("请输入课程名称（支持模糊匹配）: ").strip()
        display_tasks = filter_tasks_by_course(tasks, course_keyword)
        if not display_tasks:
            print(f"没有找到课程包含 '{course_keyword}' 的作业")
            input("\n按 Enter 键继续...")
            return tasks

    # ==========按描述筛选==========
    desc_choice = input("是否按描述搜索？(y/n，默认n): ").strip().lower()
    if desc_choice in ('y', 'yes'):
        desc_keyword = input("请输入描述关键词: ").strip().lower()
        if desc_keyword:
            # 在 display_tasks 基础上进一步筛选
            display_tasks = [t for t in display_tasks if desc_keyword in t['description'].lower()]
            if not display_tasks:
                print(f"没有找到描述包含 '{desc_keyword}' 的作业")
                input("\n按 Enter 键继续...")
                return tasks

    # ==========打印作业列表==========
    # 按截止时间排序
    sorted_tasks = sorted(display_tasks, key=lambda t: t['ddl'])

    for i, task in enumerate(sorted_tasks, 1):
        # 计算剩余天数（调用days_until()函数）
        days = days_until(task['ddl'])
        if task.get('completed'):
            status = "✅"
            color = Fore.GREEN
        elif days is None:
            status = "❓"
            color = Fore.YELLOW
        elif days < 0:
            status = "⏰"
            color = Fore.RED + Back.YELLOW
        elif days <= 3:
            status = "🔥"
            color = Fore.RED
        elif days <= 7:
            status = "⚠️"
            color = Fore.YELLOW
        else:
            status = "📌"
            color = Fore.CYAN

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

    # ==========统计信息（只针对当前显示的作业）==========
    total = len(display_tasks)
    completed = sum(1 for t in display_tasks if t.get('completed'))
    expired = sum(1 for t in display_tasks if
                  not t.get('completed') and days_until(t['ddl']) is not None and days_until(t['ddl']) < 0)
    urgent = sum(1 for t in display_tasks if
                 not t.get('completed') and days_until(t['ddl']) is not None and 0 <= days_until(t['ddl']) <= 3)

    print("\n" + "-" * 30)
    print(f"📊 显示作业数: {total}")
    print(f"✅ 已完成: {completed}")
    print(f"⏰ 已过期: {expired}")
    print(f"🔥 紧急(≤3天): {urgent}")

    # ===========按课程统计作业完成情况==========
    stats_choice = input("\n是否显示按课程统计？(y/n，默认n): ").strip().lower()
    if stats_choice in ('y', 'yes'):
        # 统计每个课程的作业数、完成数
        course_stats = {}
        for t in tasks:
            course = t['course']
            if course not in course_stats:
                course_stats[course] = {'total': 0, 'completed': 0}
            course_stats[course]['total'] += 1
            if t.get('completed'):
                course_stats[course]['completed'] += 1

        print("\n--- 按课程统计 ---")
        for course, stats in course_stats.items():
            percent = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            bar = '█' * int(percent / 10) + '░' * (10 - int(percent / 10))  # 简单进度条
            print(f"{course}: {stats['completed']}/{stats['total']} {bar} {percent:.1f}%")

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

def edit_task(tasks):
    """修改指定的作业"""
    if not tasks:
        print("暂无作业可修改")
        input("\n按 Enter 键继续...")
        return tasks

    print("\n--- 选择要修改的作业 ---")
    # 显示所有作业（带编号、状态、课程、截止时间）
    for i, task in enumerate(tasks, 1):
        status = "✅" if task.get('completed') else "⏳"
        print(f"{i}. {status} {task['course']} - 截止: {task['ddl']}")

    try:
        idx = int(input("请输入要修改的作业编号: ")) - 1
        if 0 <= idx < len(tasks):
            task = tasks[idx]  # 获取要修改的作业
            print(f"\n当前作业信息：")
            print(f"课程：{task['course']}")
            print(f"截止时间：{task['ddl']}")
            print(f"描述：{task['description']}")
            print(f"状态：{'已完成' if task.get('completed') else '未完成'}")

            print("\n请输入新的信息（直接回车表示不修改）：")

            # 修改课程
            new_course = input(f"课程名称 [{task['course']}]: ").strip()
            if new_course:
                task['course'] = new_course

            # 修改截止时间
            new_ddl = input(f"截止时间 (格式: YYYY-MM-DD HH:MM) [{task['ddl']}]: ").strip()
            if new_ddl:
                if validate_datetime(new_ddl) is not None:
                    task['ddl'] = new_ddl
                else:
                    print("❌ 日期格式错误，截止时间未修改")

            # 修改描述
            new_desc = input(f"作业描述 [{task['description']}]: ").strip()
            if new_desc:
                task['description'] = new_desc

            # 修改完成状态（标记完成功能已独立，这里可加可不加）
            # 这里也能修改状态
            change_status = input("是否修改完成状态？(y/n，默认n): ").strip().lower()
            if change_status == 'y':
                task['completed'] = not task['completed']
                print(f"状态已切换为：{'已完成' if task['completed'] else '未完成'}")

            save_tasks(tasks)
            print(f"✅ 作业修改成功")
        else:
            print("❌ 编号超出范围")
    except ValueError:
        print("❌ 请输入有效数字")

    input("\n按 Enter 键继续...")
    return tasks

def export_to_csv(tasks):
    """将作业列表导出为 CSV 文件"""
    if not tasks:
        print("暂无作业可导出")
        input("\n按 Enter 键继续...")
        return tasks

    filename = f"tasks_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['课程', '截止时间', '描述', '创建时间', '完成状态'])
        for t in tasks:
            writer.writerow([
                t['course'],
                t['ddl'],
                t['description'],
                t['created_at'],
                '已完成' if t.get('completed') else '未完成'
            ])
    print(f"✅ 已导出到 {filename}")
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
        print("5. 修改作业")
        print("6. 导出CSV格式的作业列表")
        print("7. 退出")

        choice = input("请输入数字(1-7): ").strip()

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
            tasks = edit_task(tasks)
        elif choice == "6":
            tasks = export_to_csv(tasks)
        elif choice == "7":
            print("感谢使用，再见！")
            break

        else:
            print("❌ 无效输入，请输入1-7之间的数字")


if __name__ == "__main__":
    main()
