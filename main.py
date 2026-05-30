import os
import subprocess
import re
import tkinter as tk
from tkinter import filedialog
import sys
import time

def normalize_path(path):
    """规范化路径：去除引号，处理相对路径，转换为绝对路径"""
    # 去除首尾的引号（单引号或双引号）
    path = path.strip('"').strip("'")
    
    # 处理 . 和 .. 相对路径
    if path in ['.', '.\\', './']:
        path = os.getcwd()  # 当前工作目录
    elif path in ['..', '..\\', '../']:
        path = os.path.dirname(os.getcwd())  # 上级目录
    else:
        # 转换为绝对路径
        path = os.path.abspath(path)
    
    return path

# 压缩率阈值
COMPRESSION_RATIO_THRESHOLD = 80

def get_7z_path():
    """获取脚本所在目录下的7z文件夹中的7z.exe路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    local_paths = [
        os.path.join(script_dir, "7z", "7z.exe"),
        os.path.join(script_dir, "7z.exe"),
    ]
    
    for path in local_paths:
        if os.path.exists(path):
            return path
    
    return None

def get_folder_size(folder_path):
    """计算文件夹总大小（字节）"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.exists(file_path):
                try:
                    total_size += os.path.getsize(file_path)
                except:
                    pass
    return total_size

def compress_folder(folder_path, output_path, compression_level):
    """压缩文件夹，返回是否成功和压缩后的文件大小，实时显示进度"""
    seven_zip = get_7z_path()
    if not seven_zip:
        return False, 0, "未找到7z.exe"
    
    level_name = {
        0: "仅存储(不压缩)",
        1: "最快压缩",
        5: "标准压缩",
        9: "最大压缩"
    }.get(compression_level, f"mx={compression_level}")
    
    print(f"\n🚀 开始压缩 (mx={compression_level} - {level_name})...")
    
    cmd = [
        seven_zip, "a",
        "-tzip",
        f"-mx={compression_level}",
        "-mmt=on",
        output_path,
        folder_path
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    last_percent = 0
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        
        percent_match = re.search(r'(\d+)%', line)
        if percent_match:
            percent = int(percent_match.group(1))
            if percent != last_percent:
                bar_length = 40
                filled = int(bar_length * percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"\r📦 压缩进度: [{bar}] {percent}%", end='', flush=True)
                last_percent = percent
    
    print()
    process.wait()
    
    if process.returncode == 0 and os.path.exists(output_path):
        compressed_size = os.path.getsize(output_path)
        return True, compressed_size, None
    else:
        return False, 0, f"压缩失败，返回码: {process.returncode}"

def select_output_location(default_filename):
    """弹出保存对话框，使用默认文件名"""
    root = tk.Tk()
    root.withdraw()
    
    if not default_filename.endswith('.zip'):
        default_filename += '.zip'
    
    output_path = filedialog.asksaveasfilename(
        title="保存压缩包",
        defaultextension=".zip",
        filetypes=[("ZIP压缩文件", "*.zip")],
        initialfile=default_filename
    )
    
    root.destroy()
    return output_path if output_path else None

def format_size(bytes_size):
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def get_folder_name_from_path(folder_path):
    """从路径中提取文件夹名称"""
    folder_path = folder_path.rstrip(os.sep)
    folder_name = os.path.basename(folder_path)
    
    if not folder_name:
        drive = os.path.splitdrive(folder_path)[0]
        if drive:
            folder_name = drive.rstrip(':')
        else:
            folder_name = "archive"
    
    return folder_name

def main():
    if len(sys.argv) != 2:
        print("使用方法: python main.py <目录路径>")
        print("示例: python main.py \"C:\\MyFolder\"")
        print("示例: python main.py \"M:\\美少女万华镜 -理与迷宫的少女-\"")
        print("示例: python main.py .\\MyFolder")
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 获取并规范化路径
    source_dir = normalize_path(sys.argv[1])
    
    print(f"📁 解析后的路径: {source_dir}")
    
    if not os.path.isdir(source_dir):
        print(f"❌ 错误: 目录不存在 - {source_dir}")
        input("\n按回车键退出...")
        sys.exit(1)
    
    seven_zip = get_7z_path()
    if not seven_zip:
        print("❌ 错误: 未找到 7z/7z.exe")
        print("请确保目录结构:")
        print("  脚本目录/")
        print("  ├── main.py")
        print("  └── 7z/")
        print("      ├── 7z.exe")
        print("      └── 7z.dll")
        input("\n按回车键退出...")
        sys.exit(1)
    
    print(f"📦 7z路径: {seven_zip}")
    print(f"📁 源目录: {source_dir}")
    
    print("📊 正在计算原始文件大小...")
    original_size = get_folder_size(source_dir)
    print(f"📊 原始大小: {format_size(original_size)}")
    
    default_filename = get_folder_name_from_path(source_dir)
    print(f"📝 默认文件名: {default_filename}.zip")
    
    output_path = select_output_location(default_filename)
    if not output_path:
        print("❌ 未选择保存位置")
        input("\n按回车键退出...")
        sys.exit(0)
    
    print(f"💾 输出文件: {output_path}")
    
    start_time = time.time()
    success, compressed_size, error = compress_folder(source_dir, output_path, compression_level=5)
    
    if not success:
        print(f"\n❌ 压缩失败: {error}")
        input("\n按回车键退出...")
        sys.exit(1)
    
    compression_ratio = (compressed_size / original_size * 100) if original_size > 0 else 100
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 50)
    print("📊 第一次压缩结果 (mx=5 - 标准压缩):")
    print(f"   原始大小: {format_size(original_size)}")
    print(f"   压缩后大小: {format_size(compressed_size)}")
    print(f"   压缩率: {compression_ratio:.1f}%")
    print(f"   耗时: {elapsed:.1f} 秒")
    print("=" * 50)
    
    if compression_ratio > COMPRESSION_RATIO_THRESHOLD:
        print(f"\n⚠️ 压缩率 {compression_ratio:.1f}% > {COMPRESSION_RATIO_THRESHOLD}%")
        print(f"   说明文件已经高度压缩，改用仅存储模式...")
        
        os.remove(output_path)
        print(f"🗑️ 已删除临时文件")
        
        start_time = time.time()
        success, compressed_size, error = compress_folder(source_dir, output_path, compression_level=0)
        elapsed = time.time() - start_time
        
        if not success:
            print(f"\n❌ 重新压缩失败: {error}")
            input("\n按回车键退出...")
            sys.exit(1)
        
        final_ratio = (compressed_size / original_size * 100) if original_size > 0 else 100
        final_level = 0
        
        print("\n" + "=" * 50)
        print("✅ 最终压缩结果 (mx=0 - 仅存储):")
        print(f"   原始大小: {format_size(original_size)}")
        print(f"   压缩后大小: {format_size(compressed_size)}")
        print(f"   压缩率: {final_ratio:.1f}%")
        print(f"   耗时: {elapsed:.1f} 秒")
        print("=" * 50)
    else:
        print(f"\n✅ 压缩效果良好，保持使用 mx=5")
        final_level = 5
    
    print(f"\n🎉 压缩完成！")
    print(f"📦 最终文件: {output_path}")
    print(f"📊 最终大小: {format_size(compressed_size)}")
    print(f"⚙️ 使用等级: mx={final_level}" + (" (仅存储)" if final_level == 0 else " (标准压缩)"))
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()