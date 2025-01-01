import streamlit as st
from streamlit.components.v1 import html

def render_action_buttons(disabled: bool = False) -> None:
    """渲染游戏操作按钮
    Args:
        disabled: 是否禁用按钮
    """
    col1, col2 = st.columns(2)
    
    with col1:
        hit = st.button(
            "Hit 🎯",
            key="hit",
            disabled=disabled,
            use_container_width=True,
            type="primary"
        )
    
    with col2:
        stand = st.button(
            "Stand 🛑",
            key="stand",
            disabled=disabled,
            use_container_width=True,
            type="secondary"
        )
    
    if hit:
        return "hit"
    elif stand:
        return "stand"
    return None

def render_game_stats(player_wins: int, dealer_wins: int) -> None:
    """渲染游戏统计信息
    Args:
        player_wins: 玩家胜场
        dealer_wins: 庄家胜场
    """
    stats_html = f"""
    <div style="
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
        padding: 15px;
        background: linear-gradient(135deg, #2196F3, #1976D2);
        border-radius: 12px;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    ">
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold;">
                {player_wins}
            </div>
            <div style="font-size: 14px; opacity: 0.9;">
                Player Wins
            </div>
        </div>
        
        <div style="
            width: 2px;
            background: rgba(255,255,255,0.3);
            margin: 0 15px;
        "></div>
        
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold;">
                {dealer_wins}
            </div>
            <div style="font-size: 14px; opacity: 0.9;">
                Dealer Wins
            </div>
        </div>
    </div>
    """
    
    # 使用streamlit的html组件显示
    html(stats_html, height=100)

def render_game_message(message: str, type: str = "info") -> None:
    """渲染游戏消息
    Args:
        message: 要显示的消息
        type: 消息类型 (success/error/warning/info)
    """
    # 根据消息类型设置样式
    style_map = {
        "success": ("linear-gradient(135deg, #4CAF50, #45a049)", "🎉"),
        "error": ("linear-gradient(135deg, #f44336, #d32f2f)", "❌"),
        "warning": ("linear-gradient(135deg, #ff9800, #f57c00)", "⚠️"),
        "info": ("linear-gradient(135deg, #2196F3, #1976D2)", "ℹ️")
    }
    background, icon = style_map.get(type, style_map["info"])
    
    message_html = f"""
    <div style="
        margin: 10px 0;
        padding: 15px;
        background: {background};
        border-radius: 8px;
        color: white;
        font-size: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    ">
        <span style="font-size: 20px;">{icon}</span>
        <span>{message}</span>
    </div>
    """
    
    # 使用streamlit的html组件显示
    html(message_html, height=70) 