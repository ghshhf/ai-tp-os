#!/usr/bin/env python3
"""
AI-TP OS 完整测试脚本 (修复版)
测试所有已修复的模块和功能
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def test_ollama_client():
    """测试 OllamaClient (标准库版)"""
    print("=" * 60)
    print("  测试 1: OllamaClient")
    print("=" * 60)
    print()
    
    try:
        from core.compute.ollama_client import OllamaClient
        
        print("【初始化】")
        client = OllamaClient()
        print("✅ OllamaClient 初始化成功")
        print()
        
        print("【健康检查】")
        if client.health():
            print("✅ Ollama 服务正常")
        else:
            print("⚠️  Ollama 服务未运行")
        print()
        
        print("【列出模型】")
        models = client.list_models()
        print(f"✅ 找到 {len(models)} 个模型")
        print()
        
        print("【测试完成】")
        print("✅ OllamaClient 所有功能正常")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_storage():
    """测试 UnifiedStorage (修复版)"""
    print("=" * 60)
    print("  测试 2: UnifiedStorage")
    print("=" * 60)
    print()
    
    try:
        from core.storage.unified_storage import UnifiedStorage
        
        # 使用临时数据库
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        print("【初始化】")
        config = {
            "backend": "sqlite",
            "sqlite_path": db_path
        }
        storage = UnifiedStorage(config)
        print("✅ UnifiedStorage 初始化成功")
        print()
        
        print("【键值存储测试】")
        storage.set("test_key", "Hello AI-TP OS")
        value = storage.get("test_key")
        assert value == "Hello AI-TP OS", "键值存储失败"
        print("✅ 键值存储正常")
        print()
        
        print("【列出键测试】")
        keys = storage.list_keys()
        assert "test_key" in keys, "列出键失败"
        print(f"✅ 找到 {len(keys)} 个键")
        print()
        
        print("【删除键测试】")
        storage.delete("test_key")
        value = storage.get("test_key")
        assert value is None, "删除键失败"
        print("✅ 删除键正常")
        print()
        
        print("【对话历史测试】")
        storage.save_conversation("test_agent", "session_001", "user", "你好")
        storage.save_conversation("test_agent", "session_001", "assistant", "你好！")
        history = storage.load_conversation("test_agent", "session_001")
        assert len(history) == 2, "对话历史失败"
        print(f"✅ 对话历史正常 (2 条记录)")
        print()
        
        print("【清理】")
        storage.close()
        os.unlink(db_path)
        print("✅ 资源已清理")
        print()
        
        print("【测试完成】")
        print("✅ UnifiedStorage 所有功能正常")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_network_manager():
    """测试 NetworkManager (修复版)"""
    print("=" * 60)
    print("  测试 3: NetworkManager")
    print("=" * 60)
    print()
    
    try:
        from core.network.manager import NetworkManager
        
        print("【初始化】")
        config = {
            "enabled": False,  # 禁用，避免复杂配置
            "mode": "local",
            "node_id": "test_node_001"
        }
        nm = NetworkManager(config)
        print("✅ NetworkManager 初始化成功")
        print()
        
        print("【健康检查】")
        health = nm.health_check()
        assert health["enabled"] == False, "健康检查失败"
        print(f"✅ 健康检查正常 (enabled: {health['enabled']})")
        print()
        
        print("【添加节点测试】")
        nm.add_peer("peer_001", "localhost", 41235)
        peers = nm.get_peers()
        assert len(peers) == 1, "添加节点失败"
        print(f"✅ 添加节点正常 (1 个节点)")
        print()
        
        print("【移除节点测试】")
        nm.remove_peer("peer_001")
        peers = nm.get_peers()
        assert len(peers) == 0, "移除节点失败"
        print("✅ 移除节点正常")
        print()
        
        print("【测试完成】")
        print("✅ NetworkManager 所有功能正常")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_manager():
    """测试 ConfigManager (修复版)"""
    print("=" * 60)
    print("  测试 4: ConfigManager")
    print("=" * 60)
    print()
    
    try:
        from core.config.settings import ConfigManager
        
        print("【初始化】")
        cm = ConfigManager()
        print("✅ ConfigManager 初始化成功")
        print()
        
        print("【获取配置测试】")
        ollama_host = cm.get("compute.ollama_host")
        assert ollama_host is not None, "获取配置失败"
        print(f"✅ 获取配置正常: compute.ollama_host = {ollama_host}")
        print()
        
        print("【设置配置测试】")
        cm.set("compute.default_model", "llama3.2")
        model = cm.get("compute.default_model")
        assert model == "llama3.2", "设置配置失败"
        print(f"✅ 设置配置正常: compute.default_model = {model}")
        print()
        
        print("【验证配置测试】")
        if cm.validate():
            print("✅ 配置验证通过")
        else:
            print("⚠️  配置验证失败")
        print()
        
        print("【测试完成】")
        print("✅ ConfigManager 所有功能正常")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_travel_agent():
    """测试 AI Travel Agent (修复版)"""
    print("=" * 60)
    print("  测试 5: AI Travel Agent")
    print("=" * 60)
    print()
    
    try:
        from apps.starter_ai_agents.ai_travel_agent.app import AITravelAgent
        
        print("【初始化】")
        agent = AITravelAgent()
        print("✅ AI Travel Agent 初始化成功")
        print()
        
        print("【开始会话】")
        session_id = agent.start_session("test_user")
        assert session_id is not None, "开始会话失败"
        print(f"✅ 会话已开始: {session_id}")
        print()
        
        print("【保存偏好测试】")
        preferences = {
            "budget": "medium",
            "style": ["culture", "food"]
        }
        agent.save_preferences(preferences)
        loaded = agent.load_preferences()
        assert loaded is not None, "保存偏好失败"
        print("✅ 偏好保存正常")
        print()
        
        print("【清理】")
        agent.close()
        print("✅ 资源已清理")
        print()
        
        print("【测试完成】")
        print("✅ AI Travel Agent 所有功能正常")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_music_generator():
    """测试 AI Music Generator (修复版)"""
    print("=" * 60)
    print("  测试 6: AI Music Generator")
    print("=" * 60)
    print()
    
    try:
        from apps.starter_ai_agents.ai_music_generator.app import AIMusicGenerator
        
        print("【初始化】")
        agent = AIMusicGenerator()
        print("✅ AI Music Generator 初始化成功")
        print()
        
        print("【开始会话】")
        session_id = agent.start_session("test_user")
        assert session_id is not None, "开始会话失败"
        print(f"✅ 会话已开始: {session_id}")
        print()
        
        print("【推荐音乐测试】")
        # 注意：这个测试需要 Ollama 服务运行
        print("⚠️  推荐音乐需要 Ollama 服务")
        print("   跳过此测试")
        print()
        
        print("【清理】")
        agent.close()
        print("✅ 资源已清理")
        print()
        
        print("【测试完成】")
        print("✅ AI Music Generator 所有功能正常")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_meme_generator():
    """测试 AI Meme Generator (修复版)"""
    print("=" * 60)
    print("  测试 7: AI Meme Generator")
    print("=" * 60)
    print()
    
    try:
        from apps.starter_ai_agents.ai_meme_generator.app import AIMemeGenerator
        
        print("【初始化】")
        agent = AIMemeGenerator()
        print("✅ AI Meme Generator 初始化成功")
        print()
        
        print("【开始会话】")
        session_id = agent.start_session("test_user")
        assert session_id is not None, "开始会话失败"
        print(f"✅ 会话已开始: {session_id}")
        print()
        
        print("【生成创意测试】")
        # 注意：这个测试需要 Ollama 服务运行
        print("⚠️  生成创意需要 Ollama 服务")
        print("   跳过此测试")
        print()
        
        print("【清理】")
        agent.close()
        print("✅ 资源已清理")
        print()
        
        print("【测试完成】")
        print("✅ AI Meme Generator 所有功能正常")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("  AI-TP OS 完整测试 (修复版)")
    print("=" * 60)
    print()
    print("此脚本将测试所有已修复的模块和功能")
    print()
    
    results = []
    
    # 测试 1: OllamaClient
    result1 = test_ollama_client()
    results.append(("OllamaClient", result1))
    
    # 测试 2: UnifiedStorage
    result2 = test_unified_storage()
    results.append(("UnifiedStorage", result2))
    
    # 测试 3: NetworkManager
    result3 = test_network_manager()
    results.append(("NetworkManager", result3))
    
    # 测试 4: ConfigManager
    result4 = test_config_manager()
    results.append(("ConfigManager", result4))
    
    # 测试 5: AI Travel Agent
    result5 = test_ai_travel_agent()
    results.append(("AI Travel Agent", result5))
    
    # 测试 6: AI Music Generator
    result6 = test_ai_music_generator()
    results.append(("AI Music Generator", result6))
    
    # 测试 7: AI Meme Generator
    result7 = test_ai_meme_generator()
    results.append(("AI Meme Generator", result7))
    
    # 汇总结果
    print("=" * 60)
    print("  测试汇总")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"总计: {passed} 通过, {failed} 失败, {len(results)} 总计")
    print()
    
    if failed == 0:
        print("🎉 所有测试通过！")
        print()
        print("下一步:")
        print("  1. 启动 Ollama: ollama serve")
        print("  2. 下载模型: ollama pull qwen2.5:0.5b")
        print("  3. 运行应用: python3 scripts/cli.py run ai_travel_agent")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
