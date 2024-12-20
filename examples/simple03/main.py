"""
主程序入口
"""
import streamlit as st
from game_manager import GameManager
from card_manager import CardManager
from llm_interaction import LLMInteraction

def main():
    st.set_page_config(
        page_title="LLM驱动的对话式卡牌游戏",
        layout="wide"
    )
    
    st.title("LLM驱动的对话式卡牌游戏")
    
    # 初始化游戏管理器
    if 'game_manager' not in st.session_state:
        st.session_state.game_manager = GameManager()
        st.session_state.card_manager = CardManager()
        st.session_state.llm = LLMInteraction()
    
    # 显示游戏状态
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("玩家状态")
        st.write(f"生命值: {st.session_state.game_manager.player_hp}")
        
        # 显示玩家手牌
        st.subheader("你的手牌")
        for card in st.session_state.card_manager.player_hand:
            with st.container():
                st.write(f" {card['name']}")
                st.caption(f"{card['description']}")
    
    with col2:
        st.subheader("AI状态")
        st.write(f"生命值: {st.session_state.game_manager.ai_hp}")
        st.write(f"AI手牌数量: {len(st.session_state.card_manager.ai_hand)}")
    
    # 游戏日志
    st.subheader("游戏日志")
    for log in st.session_state.game_manager.game_log[-5:]:  # 只显示最近5条日志
        st.text(log)
    
    # 用户输入
    with st.container():
        user_input = st.text_input("请输入你的指令：", placeholder="例如：使用火球术攻击对手")
        if st.button("确认", type="primary"):
            if user_input:
                # 处理用户输入
                response = st.session_state.llm.process_user_input(
                    user_input,
                    {
                        "player_hp": st.session_state.game_manager.player_hp,
                        "ai_hp": st.session_state.game_manager.ai_hp,
                        "player_hand": st.session_state.card_manager.player_hand,
                        "current_turn": st.session_state.game_manager.current_turn
                    }
                )
                st.write(f"AI响应: {response}")

if __name__ == "__main__":
    main()
