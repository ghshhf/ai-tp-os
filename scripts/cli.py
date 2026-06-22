#!/usr/bin/env python3
"""
AI-TP OS CLI 工具 (修复版)
提供命令行接口管理 AI-TP OS 系统
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config.settings import get_config, load_config
from core.compute.ollama_client import OllamaClient
from core.storage.unified_storage import UnifiedStorage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_tp_cli')


def cmd_status(args):
    """查看系统状态 (修复版)"""
    try:
        config = load_config()
        
        print("=" * 60)
        print("  AI-TP OS 系统状态")
        print("=" * 60)
        print()
        
        # 检查配置
        print("【配置】")
        print(f"  配置文件: {config.get('config_path', '默认')}")
        print(f"  计算后端: {config.get('compute', {}).get('backend', '未知')}")
        print(f"  存储后端: {config.get('storage', {}).get('backend', '未知')}")
        print(f"  网络模式: {config.get('network', {}).get('mode', '未知')}")
        print()
        
        # 检查 Ollama
        print("【Ollama】")
        ollama_host = config.get('compute', {}).get('ollama_host', 'http://localhost:11434')
        client = OllamaClient(host=ollama_host)
        
        if client.health():
            print(f"  状态: ✅ 正常")
            models = client.list_models()
            print(f"  模型数: {len(models)}")
            if models:
                print(f"  默认模型: {models[0].get('name', '未知')}")
        else:
            print(f"  状态: ❌ 无法连接 ({ollama_host})")
            print(f"  提示: 请启动 Ollama 服务")
        print()
        
        # 检查存储
        print("【存储】")
        storage_config = config.get('storage', {})
        storage = UnifiedStorage(storage_config)
        
        backend = storage_config.get('backend', '未知')
        print(f"  后端: {backend}")
        
        # 测试存储
        test_key = "_status_test_"
        if storage.set(test_key, "test"):
            value = storage.get(test_key)
            if value == "test":
                print(f"  状态: ✅ 正常")
            else:
                print(f"  状态: ⚠️  读写异常")
            storage.delete(test_key)
        else:
            print(f"  状态: ❌ 写入失败")
        
        storage.close()
        print()
        
        # 检查网络
        print("【网络】")
        network_config = config.get('network', {})
        enabled = network_config.get('enabled', False)
        print(f"  启用: {enabled}")
        if enabled:
            print(f"  模式: {network_config.get('mode', '未知')}")
            print(f"  节点 ID: {network_config.get('node_id', '未知')}")
        print()
        
        print("=" * 60)
        print("  状态检查完成")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 状态检查失败: {e}")
        return 1
    
    return 0


def cmd_init(args):
    """初始化系统 (修复版)"""
    try:
        print("=" * 60)
        print("  AI-TP OS 初始化")
        print("=" * 60)
        print()
        
        # 创建必要目录
        dirs = ["data", "models", "logs", "config"]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
            print(f"✅ 目录已创建: {d}/")
        
        print()
        
        # 创建默认配置文件
        config_path = args.config or "ai-tp-config.yaml"
        
        if os.path.exists(config_path) and not args.force:
            print(f"⚠️  配置文件已存在: {config_path}")
            print(f"   使用 --force 强制覆盖")
            return 1
        
        default_config = {
            "compute": {
                "backend": "ollama",
                "ollama_host": "http://localhost:11434",
                "default_model": "qwen2.5:0.5b",
                "timeout": 120,
            },
            "storage": {
                "backend": "sqlite",
                "sqlite_path": str(Path("data") / "ai-tp.db"),
            },
            "network": {
                "enabled": False,
                "mode": "local",
                "node_id": None,
                "discovery_interval": 60,
            },
            "logging": {
                "level": "INFO",
            },
        }
        
        # 保存配置
        import yaml
        
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ 配置文件已创建: {config_path}")
        print()
        
        # 提示下一步
        print("【下一步】")
        print("  1. 启动 Ollama: ollama serve")
        print("  2. 下载模型: ollama pull qwen2.5:0.5b")
        print("  3. 查看状态: ai-tp status")
        print()
        
        print("=" * 60)
        print("  初始化完成")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        return 1
    
    return 0


def cmd_model(args):
    """模型管理 (修复版)"""
    try:
        config = load_config()
        ollama_host = config.get('compute', {}).get('ollama_host', 'http://localhost:11434')
        client = OllamaClient(host=ollama_host)
        
        if args.action == "list":
            # 列出模型
            print("=" * 60)
            print("  本地模型列表")
            print("=" * 60)
            print()
            
            models = client.list_models()
            
            if not models:
                print("⚠️  没有本地模型")
                print()
                print("【下载模型】")
                print("  ollama pull qwen2.5:0.5b")
                print("  ollama pull llama3.2")
                print()
            else:
                for i, model in enumerate(models, 1):
                    name = model.get('name', '未知')
                    size = model.get('size', 0)
                    if size > 1024 * 1024 * 1024:
                        size_str = f"{size / (1024**3):.1f} GB"
                    else:
                        size_str = f"{size / (1024**2):.1f} MB"
                    
                    print(f"{i}. {name}")
                    print(f"   大小: {size_str}")
                    print(f"   修改时间: {model.get('modified_at', '未知')}")
                    print()
            
            print("=" * 60)
            
        elif args.action == "pull":
            # 拉取模型
            if not args.model:
                print("❌ 请指定模型名称")
                print("   示例: ai-tp model pull qwen2.5:0.5b")
                return 1
            
            print(f"正在拉取模型: {args.model}")
            print("这可能需要几分钟...")
            print()
            
            for progress in client.pull_model(args.model, stream=True):
                try:
                    data = json.loads(progress)
                    status = data.get('status', '')
                    print(f"\r{status}", end='', flush=True)
                except json.JSONDecodeError:
                    pass
            
            print()
            print(f"✅ 模型已拉取: {args.model}")
            
        elif args.action == "delete":
            # 删除模型
            if not args.model:
                print("❌ 请指定模型名称")
                print("   示例: ai-tp model delete qwen2.5:0.5b")
                return 1
            
            print(f"正在删除模型: {args.model}")
            # TODO: 实现删除功能
            print("⚠️  删除功能尚未实现")
            print("   请手动删除: ollama rm <model>")
            
        else:
            print(f"❌ 未知操作: {args.action}")
            return 1
        
    except Exception as e:
        logger.error(f"❌ 模型管理失败: {e}")
        return 1
    
    return 0


def cmd_storage(args):
    """存储管理 (修复版)"""
    try:
        config = load_config()
        storage_config = config.get('storage', {})
        storage = UnifiedStorage(storage_config)
        
        if args.action == "list":
            # 列出键
            print("=" * 60)
            print("  存储键列表")
            print("=" * 60)
            print()
            
            keys = storage.list_keys(prefix=args.prefix or "")
            
            if not keys:
                print("⚠️  没有数据")
            else:
                for i, key in enumerate(keys, 1):
                    value = storage.get(key)
                    value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"{i}. {key}: {value_str}")
                print()
                print(f"总计: {len(keys)} 个键")
            
            print("=" * 60)
            
        elif args.action == "get":
            # 获取值
            if not args.key:
                print("❌ 请指定键名")
                return 1
            
            value = storage.get(args.key)
            
            if value is None:
                print(f"⚠️  键不存在: {args.key}")
            else:
                print(json.dumps(value, ensure_ascii=False, indent=2))
            
        elif args.action == "set":
            # 设置值
            if not args.key or not args.value:
                print("❌ 请指定键名和值")
                return 1
            
            # 尝试解析 JSON
            try:
                value = json.loads(args.value)
            except json.JSONDecodeError:
                value = args.value
            
            if storage.set(args.key, value):
                print(f"✅ 已设置: {args.key} = {value}")
            else:
                print(f"❌ 设置失败: {args.key}")
                return 1
            
        elif args.action == "delete":
            # 删除键
            if not args.key:
                print("❌ 请指定键名")
                return 1
            
            if storage.delete(args.key):
                print(f"✅ 已删除: {args.key}")
            else:
                print(f"⚠️  键不存在: {args.key}")
            
        else:
            print(f"❌ 未知操作: {args.action}")
            return 1
        
        storage.close()
        
    except Exception as e:
        logger.error(f"❌ 存储管理失败: {e}")
        return 1
    
    return 0


def cmd_run(args):
    """运行应用 (修复版)"""
    try:
        app_name = args.app
        
        print("=" * 60)
        print(f"  运行应用: {app_name}")
        print("=" * 60)
        print()
        
        # 查找应用
        app_path = Path("apps") / "starter_ai_agents" / app_name / "app.py"
        
        if not app_path.exists():
            print(f"❌ 应用不存在: {app_name}")
            print()
            print("【可用应用】")
            print("  ai_travel_agent  - 旅行规划助手")
            print("  ai_music_generator - 音乐生成助手")
            print("  ai_meme_generator - 梗图生成助手")
            print()
            return 1
        
        print(f"正在启动应用: {app_name}")
        print("...")
        
        # 运行应用
        os.execv(sys.executable, [sys.executable, str(app_path)] + args.args)
        
    except Exception as e:
        logger.error(f"❌ 应用运行失败: {e}")
        return 1
    
    return 0


def main():
    """主入口 (修复版)"""
    parser = argparse.ArgumentParser(
        description="AI-TP OS CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ai-tp status          查看系统状态
  ai-tp init            初始化系统
  ai-tp model list      列出模型
  ai-tp model pull MODEL  拉取模型
  ai-tp storage list    列出存储键
  ai-tp run APP        运行应用
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="查看系统状态")
    status_parser.set_defaults(func=cmd_status)
    
    # init 命令
    init_parser = subparsers.add_parser("init", help="初始化系统")
    init_parser.add_argument("--config", help="配置文件路径")
    init_parser.add_argument("--force", action="store_true", help="强制覆盖")
    init_parser.set_defaults(func=cmd_init)
    
    # model 命令
    model_parser = subparsers.add_parser("model", help="模型管理")
    model_parser.add_argument("action", choices=["list", "pull", "delete"], help="操作")
    model_parser.add_argument("model", nargs="?", help="模型名称")
    model_parser.set_defaults(func=cmd_model)
    
    # storage 命令
    storage_parser = subparsers.add_parser("storage", help="存储管理")
    storage_parser.add_argument("action", choices=["list", "get", "set", "delete"], help="操作")
    storage_parser.add_argument("key", nargs="?", help="键名")
    storage_parser.add_argument("value", nargs="?", help="值")
    storage_parser.add_argument("--prefix", help="键前缀")
    storage_parser.set_defaults(func=cmd_storage)
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行应用")
    run_parser.add_argument("app", help="应用名称")
    run_parser.add_argument("args", nargs=argparse.REMAINDER, help="应用参数")
    run_parser.set_defaults(func=cmd_run)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
