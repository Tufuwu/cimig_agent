"""异常体系"""

class CIMIGAgentsException(Exception):
    """CIMIGAgents基础异常类"""
    pass

class LLMException(CIMIGAgentsException):
    """LLM相关异常"""
    pass

class AgentException(CIMIGAgentsException):
    """Agent相关异常"""
    pass

class ConfigException(CIMIGAgentsException):
    """配置相关异常"""
    pass

class ToolException(CIMIGAgentsException):
    """工具相关异常"""
    pass