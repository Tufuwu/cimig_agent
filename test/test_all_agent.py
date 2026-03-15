import pytest
import os
from dotenv import load_dotenv
from cimig_agent import CimigAgent,CIMIGAgentsLLM


load_dotenv()
class TestEnvironment:
    def test_env_variables(self):
        """验证必要的环境变量已配置"""
        api_key = os.getenv("OPENAI_API_KEY")
        assert api_key is not None, "请配置 OPENAI_API_KEY 环境变量"
        assert len(api_key) > 0, "OPENAI_API_KEY 不能为空"
        print(f"\n✅ 环境变量配置正常")
    
    def test_llm_initialization(self):
        """验证LLM可以正常初始化"""
        try:
            llm = CIMIGAgentsLLM()
            ciagent = CimigAgent(
                name="基础助手",
                llm=llm
                )
            assert ciagent is not None
            # ciagent.run("你好，请介绍一下自己")
            # print(f"\n✅ LLM初始化成功",ciagent.tool_registry.get_all_tools)
            print(ciagent.tool_registry.get_tool("read_tool").run_with_timing({"file_path":"D:/vscode/3/CIFix/CIFix/resources/actions/js/x-profiler/xprofiler-console/fixed_file.yml"}))
        except Exception as e:
            pytest.fail(f"LLM初始化失败: {e}")

if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short", "--capture=no"])