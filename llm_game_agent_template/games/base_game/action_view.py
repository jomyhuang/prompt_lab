import streamlit as st
from agent_tool import add_system_message, add_user_message, add_assistant_message
from langgraph.types import Command

def render_action_view():
    """渲染玩家操作界面"""
    if not st.session_state.game_started:
        return
    
    game_state = st.session_state.game_agent.get_game_state()
    
    if game_state["current_turn"] == "player":
        st.markdown("### 🎮 你的回合")
        
        button_cols = st.columns(3)
        valid_actions = game_state["valid_actions"]
        
        with button_cols[0]:
            if "play" in valid_actions and st.button("出牌", key="play", use_container_width=True):
                add_user_message("出牌")
                # 修改为gui_feedback
                st.session_state.gui_feedback = "play"
                st.session_state.gui_feedback_params = {
                    "phase": "play this card"
                }
                st.session_state.require_update = True
        
        with button_cols[1]:
            if "end_turn" in valid_actions and st.button("结束回合", key="end_turn", use_container_width=True):
                add_user_message("结束回合")
                st.session_state.gui_feedback = "end_turn"
                st.session_state.gui_feedback_params = {
                    "phase": "end turn phase"
                }
                st.session_state.require_update = True
                
            if st.button("结束游戏", key="game_over", use_container_width=True):
                add_user_message("结束游戏")
                st.session_state.gui_feedback = "game_over"
                st.session_state.gui_feedback_params = {
                    "phase": "game over",
                    "game_over": True
                }
                # st.session_state.game_started = False
                st.session_state.require_update = True

            if st.button("chat test", key="chat_test", use_container_width=True):
                add_user_message("chat test")
                st.session_state.gui_feedback = "chat"
                st.session_state.gui_feedback_params = {
                    "info": "say hello"
                }

                # st.session_state.game_started = False
                st.session_state.require_update = True

            