import os
from datetime import datetime
from agent.graph import create_agent_app

# 1. 编译 Graph App
app = create_agent_app()

def save_migration_report(messages, repo_path):
    """
    将对话过程格式化为 Markdown 并保存到仓库目录
    """
    report_path = os.path.join(repo_path, "migration_report.md")
    content = f"# CI/CD Migration Report\n*Generated on: {datetime.now()}*\n\n"
    
    for m in messages:
        role = m.type.upper()
        # 过滤掉空的或纯工具调用的消息，让报告更可读
        if m.content:
            content += f"### {role}\n{m.content}\n\n"
    
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"--- Report saved to {report_path} ---")
    except Exception as e:
        print(f"--- Failed to save report: {e} ---")

def run_migration(target_repo_path: str, github_token: str):
    """
    执行迁移主循环
    """
    # 2. 初始化完整的 AgentState
    # 显式提供所有字段，确保 Graph 运行过程中逻辑一致
    initial_state = {
        "messages": [
            ("system", "You are a DevOps assistant. Expert in CI/CD migrations."),
            ("user", f"The Travis CI config is in '{target_repo_path}'. "
                     f"Please migrate it to GitHub Actions and push the changes. ")
        ],
        "loop_count": 0,
        "repo_path": target_repo_path,
        "last_action_successful": True,
        "error_summary": None
    }

    # 3. 配置运行参数（如递归限制）
    config = {"recursion_limit": 25}

    print(f"--- Starting Migration for: {target_repo_path} ---")
    
    final_state = None
    # 4. 流式输出执行过程
    for event in app.stream(initial_state, config):
        for value in event.values():
            # 打印当前节点输出的消息
            if "messages" in value:
                last_msg = value["messages"][-1]
                last_msg.pretty_print()
            # 记录最后的状态以便后续保存
            final_state = value

    # 5. 任务结束后保存日志/报告
    if final_state and "messages" in final_state:
        save_migration_report(final_state["messages"], target_repo_path)

if __name__ == "__main__":
    # 配置你的环境变量或直接输入
    REPO_PATH = "./my-local-project"  # 你的本地仓库路径
    TOKEN = os.getenv("GITHUB_TOKEN", "your_token_here")
    
    if not os.path.exists(REPO_PATH):
        print(f"Error: Path {REPO_PATH} does not exist.")
    else:
        run_migration(REPO_PATH)