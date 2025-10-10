"""
测试运行脚本
"""
import os
import sys
import subprocess
import argparse


def run_command(command):
    """运行命令并返回结果"""
    print(f"运行命令: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行测试套件")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="只运行单元测试"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="只运行集成测试"
    )
    parser.add_argument(
        "--cov",
        action="store_true",
        help="生成覆盖率报告"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="生成HTML覆盖率报告"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="运行特定测试文件"
    )
    parser.add_argument(
        "--function",
        type=str,
        help="运行特定测试函数"
    )
    
    args = parser.parse_args()
    
    # 构建pytest命令
    pytest_args = ["python", "-m", "pytest"]
    
    # 添加详细输出
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")
    
    # 添加覆盖率选项
    if args.cov or args.html:
        pytest_args.extend([
            "--cov=app",
            "--cov-report=term-missing"
        ])
        
        if args.html:
            pytest_args.append("--cov-report=html:htmlcov")
    
    # 添加标记过滤
    if args.unit and not args.integration:
        pytest_args.extend(["-m", "unit"])
    elif args.integration and not args.unit:
        pytest_args.extend(["-m", "integration"])
    
    # 添加特定文件或函数
    if args.file:
        pytest_args.append(args.file)
    
    if args.function:
        pytest_args.extend(["-k", args.function])
    
    # 运行测试
    returncode = run_command(pytest_args)
    
    # 如果生成了HTML覆盖率报告，显示路径
    if args.html and returncode == 0:
        print("\nHTML覆盖率报告已生成: htmlcov/index.html")
    
    return returncode


if __name__ == "__main__":
    sys.exit(main())