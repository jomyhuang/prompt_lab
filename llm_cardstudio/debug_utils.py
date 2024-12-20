import streamlit as st
from typing import Any, List, Dict, Optional
import json
from datetime import datetime

class DebugUtils:
    """调试工具类，用于统一管理调试信息的输出"""
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
    
    def log(self, category: str, message: str, data: Optional[Any] = None):
        """记录调试信息
        
        Args:
            category: 日志类别（如 'card', 'game', 'ui' 等）
            message: 日志消息
            data: 相关数据（可选）
        """
        if not self.debug_mode:
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = {
            "timestamp": timestamp,
            "category": category,
            "message": message,
            "data": data
        }
        
        # 添加到session state中保存
        st.session_state.debug_logs.append(log_entry)
        
        # 同时打印到控制台
        print(f"[{timestamp}] [{category}] {message}")
        if data:
            print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    def get_logs(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """获取指定类别的日志
        
        Args:
            category: 日志类别（如果为None，返回所有类别）
            limit: 返回的日志条数限制
            
        Returns:
            符合条件的日志列表
        """
        logs = st.session_state.debug_logs
        if category:
            logs = [log for log in logs if log["category"] == category]
        return logs[-limit:]
    
    def clear_logs(self):
        """清空日志"""
        st.session_state.debug_logs = []
    
    def render_debug_panel(self):
        """在Streamlit侧边栏渲染调试面板"""
        with st.sidebar:
            with st.expander("🔍 调试面板", expanded=False):
                # 显示最近的日志
                st.write("最近的调试日志：")
                logs = self.get_logs(limit=10)
                for log in logs:
                    st.text(f"[{log['timestamp']}] [{log['category']}]")
                    st.text(f"Message: {log['message']}")
                    if log['data']:
                        st.json(log['data'])
                    st.markdown("---")
                
                # 清空日志按钮
                if st.button("清空日志"):
                    self.clear_logs()
                    st.success("日志已清空")

# 创建全局调试工具实例
debug_utils = DebugUtils()
