"""
AI-TP OS - 命令行接口
以底层系统为本体，整合应用层操作
"""

import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config.settings import get_config, reload_config
from core.compute.ollama_client import OllamaClient
from core.storage.unified_storage import UnifiedStorage

app = typer.Typer(help="AI-TP OS: AI-Native Decentralized OS")
console = Console()


@app.callback()
def callback():
    """AI-TP OS 命令行工具"""
    pass


@app.command()
def status():
    """查看系统状态"""
    config = get_config()

    table = Table(title="AI-TP OS 系统状态")
    table.add_column("组件", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("详情", style="yellow")

    # 推理后端状态
    ollama = OllamaClient()
    ollama_health = "[green]运行中[/green]" if ollama.health() else "[red]未启动[/red]"
    models = ollama.list_models()
    table.add_row("Ollama 推理", ollama_health, f"{len(models)} 个模型已加载")

    # 存储状态
    storage = UnifiedStorage(config.storage)
    table.add_row("统一存储", "[green]运行中[/green]", f"后端: {config.storage.backend}")

    # 网络状态
    network_status = "[green]启用[/green]" if config.network.enabled else "[red]禁用[/red]"
    table.add_row("网络层", network_status, f"模式: {config.network.mode}")

    # 调度器状态
    scheduler_status = "[green]启用[/green]" if config.scheduler.enabled else "[yellow]未启用[/yellow]"
    table.add_row("任务调度", scheduler_status, f"后端: {config.scheduler.backend}")

    console.print(table)


@app.command()
def init(
    path: str = typer.Option(".", "--path", "-p", help="初始化路径"),
    template: str = typer.Option("starter", "--template", "-t", help="模板类型"),
):
    """初始化 AI-TP OS 环境"""
    console.print(Panel.fit("[bold blue]AI-TP OS 初始化[/bold blue]"))

    target = Path(path).resolve()
    target.mkdir(parents=True, exist_ok=True)

    # 创建 .env 文件
    env_file = target / ".env"
    if not env_file.exists():
        example = Path(__file__).parent.parent / ".env.example"
        if example.exists():
            env_file.write_text(example.read_text())
            console.print(f"[green]已创建[/green] {env_file}")

    # 创建配置目录
    config_dir = target / ".ai-tp"
    config_dir.mkdir(exist_ok=True)

    console.print(f"[bold green]初始化完成![/bold green] 路径: {target}")
    console.print("\n下一步:")
    console.print("  1. 编辑 .env 文件，配置 API Key")
    console.print("  2. 运行 [bold]ai-tp model pull llama3.2[/bold] 下载模型")
    console.print("  3. 运行 [bold]ai-tp run <app_name>[/bold] 启动应用")


@app.command()
def model(
    action: str = typer.Argument(..., help="操作: list, pull, rm"),
    name: str = typer.Argument(None, help="模型名称"),
):
    """模型管理"""
    client = OllamaClient()

    if action == "list":
        models = client.list_models()
        table = Table(title="本地模型")
        table.add_column("名称", style="cyan")
        table.add_column("大小", style="yellow")
        table.add_column("修改时间", style="green")

        for m in models:
            table.add_row(
                m.get("name", "unknown"),
                m.get("size", "unknown"),
                m.get("modified_at", "unknown"),
            )
        console.print(table)

    elif action == "pull":
        if not name:
            console.print("[red]错误: 请指定模型名称[/red]")
            raise typer.Exit(1)
        console.print(f"[blue]正在下载模型 {name}...[/blue]")
        for line in client.pull_model(name):
            console.print(line)

    elif action == "rm":
        if not name:
            console.print("[red]错误: 请指定模型名称[/red]")
            raise typer.Exit(1)
        # TODO: 实现删除模型
        console.print(f"[yellow]删除模型 {name}[/yellow]")

    else:
        console.print(f"[red]未知操作: {action}[/red]")


@app.command()
def run(
    app_name: str = typer.Argument(..., help="应用名称"),
    backend: str = typer.Option("ollama", "--backend", "-b", help="推理后端"),
    port: int = typer.Option(3000, "--port", "-p", help="服务端口"),
):
    """运行 AI 应用"""
    config = get_config()

    # 查找应用
    app_path = None
    for registry in config.apps.get("registry", []):
        app_dir = Path(registry["path"]) / app_name
        if app_dir.exists():
            app_path = app_dir
            break

    if not app_path:
        console.print(f"[red]错误: 找不到应用 {app_name}[/red]")
        console.print("可用应用:")
        for registry in config.apps.get("registry", []):
            for app in registry.get("apps", []):
                console.print(f"  - {app}")
        raise typer.Exit(1)

    console.print(Panel.fit(f"[bold blue]启动应用: {app_name}[/bold blue]"))
    console.print(f"路径: {app_path}")
    console.print(f"后端: {backend}")
    console.print(f"端口: {port}")

    # 检查是否有 streamlit 应用
    streamlit_file = app_path / "app.py"
    if streamlit_file.exists():
        console.print(f"[green]检测到 Streamlit 应用[/green]")
        os.environ["STREAMLIT_SERVER_PORT"] = str(port)
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(streamlit_file)])
        return

    # 检查是否有 main.py
    main_file = app_path / "main.py"
    if main_file.exists():
        console.print(f"[green]运行 main.py[/green]")
        subprocess.run([sys.executable, str(main_file)])
        return

    console.print("[red]错误: 找不到入口文件[/red]")


@app.command()
def storage(
    action: str = typer.Argument(..., help="操作: list, get, put, del"),
    key: str = typer.Argument(None, help="键"),
    value: str = typer.Argument(None, help="值"),
    namespace: str = typer.Option("default", "--namespace", "-n", help="命名空间"),
):
    """存储管理"""
    config = get_config()
    store = UnifiedStorage(config.storage)

    if action == "list":
        keys = store.list_keys(prefix=key or "", namespace=namespace)
        table = Table(title=f"存储键列表 ({namespace})")
        table.add_column("键", style="cyan")
        for k in keys:
            table.add_row(k)
        console.print(table)

    elif action == "get":
        if not key:
            console.print("[red]错误: 请指定键[/red]")
            raise typer.Exit(1)
        data = store.get(key, namespace)
        if data:
            console.print(data)
        else:
            console.print("[yellow]键不存在[/yellow]")

    elif action == "put":
        if not key or value is None:
            console.print("[red]错误: 请指定键和值[/red]")
            raise typer.Exit(1)
        store.put(key, value, namespace)
        console.print(f"[green]已存储[/green] {key}")

    elif action == "del":
        if not key:
            console.print("[red]错误: 请指定键[/red]")
            raise typer.Exit(1)
        store.delete(key, namespace)
        console.print(f"[green]已删除[/green] {key}")


@app.command()
def config_reload():
    """重新加载配置"""
    reload_config()
    console.print("[green]配置已重新加载[/green]")


def main():
    app()


if __name__ == "__main__":
    main()
