import os
import subprocess
import re
import tkinter as tk
from tkinter import filedialog
import sys
import time

# 版本号
VERSION = "1.0.0"

# 压缩率阈值，超过此值说明文件已经很难压缩，改用仅存储模式
COMPRESSION_RATIO_THRESHOLD = 80  # 可调整的宏变量

def get_7z_path():
    """获取脚本所在目录下的7z文件夹中的7z.exe路径（支持PyInstaller打包）"""
    
    # 判断是否为打包后的exe运行
    if getattr(sys, 'frozen', False):
        # 打包后的exe运行，exe所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 正常Python脚本运行
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试多个可能的位置
    local_paths = [
        os.path.join(base_dir, "7z", "7z.exe"),
        os.path.join(base_dir, "7z.exe"),
        # 如果exe在子目录，向上查找
        os.path.join(os.path.dirname(base_dir), "7z", "7z.exe"),
        os.path.join(os.path.dirname(base_dir), "7z.exe"),
    ]
    
    # 打包后的临时目录（PyInstaller）
    if getattr(sys, 'frozen', False):
        temp_paths = [
            os.path.join(sys._MEIPASS, "7z", "7z.exe"),
            os.path.join(sys._MEIPASS, "7z.exe"),
        ]
        local_paths.extend(temp_paths)
    
    for path in local_paths:
        if os.path.exists(path):
            return path
    
    return None

def resolve_path(input_path):
    """
    解析路径，支持相对路径和绝对路径
    - 如果输入是绝对路径，直接返回
    - 如果输入是相对路径，相对于当前工作目录解析
    """
    if os.path.isabs(input_path):
        return os.path.normpath(input_path)
    else:
        # 相对路径：相对于当前工作目录
        return os.path.normpath(os.path.abspath(input_path))

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
    """压缩文件夹，返回是否成功和压缩后的文件大小，直接显示7z原始输出"""
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
    print("-" * 60)
    
    cmd = [
        seven_zip, "a",
        "-tzip",
        f"-mx={compression_level}",
        "-mmt=on",
        output_path,
        folder_path
    ]
    
    # 直接输出到控制台，不做任何处理
    process = subprocess.Popen(
        cmd,
        stdout=None,  # 直接输出到父进程的标准输出
        stderr=None,  # 直接输出到父进程的标准错误
        shell=False
    )
    
    process.wait()
    print("-" * 60)
    
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

def print_usage():
    """打印使用说明"""
    print("=" * 60)
    print(f"📦 自动压缩工具 v{VERSION}")
    print("=" * 60)
    print("使用方法:")
    print("  python main.py <目录路径>")
    print("  autoCompression.exe <目录路径>")
    print()
    print("参数:")
    print("  <目录路径>    要压缩的目录路径（支持相对路径和绝对路径）")
    print("  -v, --version 显示版本号")
    print("  -h, --help    显示此帮助信息")
    print()
    print("示例:")
    print("  python main.py C:\\MyFolder          # 绝对路径")
    print("  python main.py ..\\MyFolder          # 相对路径（上级目录）")
    print("  python main.py .\\MyFolder           # 相对路径（当前目录）")
    print("  python main.py MyFolder             # 相对路径（当前目录下的文件夹）")
    print("  python main.py -v                   # 显示版本号")
    print("=" * 60)

def main():
    # 处理帮助和版本参数
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ['-v', '--version', '-V']:
            print(f"autoCompression v{VERSION}")
            sys.exit(0)
        elif arg in ['-h', '--help', '/?']:
            print_usage()
            sys.exit(0)
    
    if len(sys.argv) != 2:
        print("❌ 错误: 参数不正确")
        print_usage()
        input("\n按回车键退出...")
        sys.exit(1)
    
    # 解析路径（支持相对路径和绝对路径）
    source_dir_input = sys.argv[1]
    source_dir = resolve_path(source_dir_input)
    
    print(f"📂 输入路径: {source_dir_input}")
    print(f"📂 解析后的绝对路径: {source_dir}")
    
    if not os.path.isdir(source_dir):
        print(f"❌ 错误: 目录不存在 - {source_dir}")
        print(f"   请检查路径是否正确")
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
    
    # 第一次压缩
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
    
    # 判断是否需要重新压缩
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
    

    
if __name__ == "__main__":
    main()