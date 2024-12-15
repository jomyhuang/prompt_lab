import streamlit as st
from llm_interaction import LLMInteraction
from game_manager import GameManager
from player_manager import PlayerManager
from debug_utils import debug_utils

# 初始化全局session state
if 'initialized' not in st.session_state:
    st.session_state.game_manager = GameManager()
    st.session_state.llm_interaction = LLMInteraction()
    st.session_state.player_manager = PlayerManager()
    st.session_state.messages = [{"role": "assistant", "content": "准备好战斗了吗？"}]
    st.session_state.initialized = True

def update_ui_state(show_success_message=None):
    """更新界面状态
    Args:
        show_success_message (str, optional): 如果提供，显示成功消息
    """
    if show_success_message:
        st.success(show_success_message)
    st.rerun()

def process_user_input_ai(user_input):
    """AI处理用户输入"""
    # 获取当前游戏状态
    game_state = st.session_state.game_manager.get_game_state()
    
    # 记录调试信息
    debug_utils.log("llm", "处理用户输入", {
        "用户输入": user_input,
        "游戏状态": game_state
    })
    
    # 在右上角显示运行状态
    with st.status("AI思考中...", expanded=False) as status:
        # 生成AI响应
        ai_response = st.session_state.llm_interaction.generate_ai_response(user_input, game_state)
        status.update(label="完成", state="complete")
    
    # 添加AI响应到消息历史
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # 记录调试信息
    debug_utils.log("llm", "AI响应", {"响应内容": ai_response})

def process_user_input(user_input):
    """处理用户输入"""
    with st.spinner("处理中..."):
        # 解析用户输入
        action_result = st.session_state.llm_interaction.parse_user_action(user_input)
        
        # 如果是使用卡牌的操作，将卡牌从手牌移到场上
        if "使用" in user_input and "卡牌" in user_input:
            selected_card = st.session_state.get("card_select")
            if selected_card:
                debug_utils.log("card", "选中卡牌", selected_card)
                
                # 使用卡牌
                result = st.session_state.game_manager.play_card(selected_card)
                if isinstance(result, dict) and result.get("removed_cards"):
                    # 简化移除卡牌的显示
                    removed_names = [card['name'] for card in result["removed_cards"]]
                    debug_utils.log("card", "移除卡牌", removed_names)
                
                if isinstance(result, dict) and result.get("status") == "success":
                    success_message = f"成功使用卡牌：{selected_card}"
                    if result.get("message"):
                        success_message += f"\n{result['message']}"
                    update_ui_state(success_message)
                else:
                    # 显示错误信息
                    st.error(result if isinstance(result, str) else "使用卡牌失败")
        
        # 更新游戏状态
        st.session_state.game_manager.update_game_state(action_result)

def render_game_view():
    """渲染游戏画面"""
    st.header("🎮 卡牌战场", divider="rainbow")
    
    # 直接从game_manager获取状态
    game_state = st.session_state.game_manager.get_game_state()
    
    # 渲染游戏控制区域
    render_game_controls()
    
    # 在侧边栏添加状态显示和更新按钮
    with st.sidebar:
        st.header("🛠️ 游戏控制台")
        if st.button("手动更新界面"):
            update_ui_state("手动更新界面")
            
        # 使用expander显示游戏状态
        with st.expander("🔍 查看游戏状态", expanded=True):
            st.json(game_state)
    
    # 显示回合信息
    st.caption(f"第 {game_state['turn_info']['current_turn']} 回合 - {'我方回合' if game_state['turn_info']['active_player'] == 'player' else '对手回合'}")
    
    # 显示对手状态
    st.markdown("### 🤖 对手状态")
    opponent_stats = game_state.get("opponent_stats", {})
    opponent_deck = game_state.get("deck_cards", {}).get("opponent", [])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.caption("生命值")
        st.markdown(f"❤️ {opponent_stats.get('hp', 0)}")
    with col2:
        st.caption("能量")
        st.markdown(f"⚡ {opponent_stats.get('energy', 0)}")
    with col3:
        st.caption("护甲")
        st.markdown(f"🛡️ {opponent_stats.get('armor', 0)}")
    with col4:
        st.caption("牌堆")
        st.markdown(f"🎴 {len(opponent_deck)}")
    
    # 对手场上卡牌
    st.markdown("#### 🎯 对手场上卡牌")
    opponent_field_cards = game_state.get("field_cards", {}).get("opponent", [])
    if not opponent_field_cards:
        st.caption("对手场上暂无卡牌")
    else:
        cols = st.columns(len(opponent_field_cards))
        for idx, card in enumerate(opponent_field_cards):
            with cols[idx]:
                st.markdown(f"""
                    **{card.get('name', '未知卡牌')}**  
                    *{card.get('type', '未知类型')}*  
                    效果: {card.get('effect', '无')}  
                    状态: {card.get('status', '未知状态')}
                """)
    
    # 分隔线
    st.divider()
    
    # 我方场上卡牌
    st.markdown("#### 🎯 我方场上卡牌")
    player_field_cards = game_state.get("field_cards", {}).get("player", [])
    if not player_field_cards:
        st.caption("我方场上暂无卡牌")
    else:
        cols = st.columns(len(player_field_cards))
        for idx, card in enumerate(player_field_cards):
            with cols[idx]:
                st.markdown(f"""
                    **{card.get('name', '未知卡牌')}**  
                    *{card.get('type', '未知类型')}*  
                    效果: {card.get('effect', '无')}  
                    状态: {card.get('status', '未知状态')}
                """)
    
    # 显示玩家状态
    st.markdown("### 👤 我方状态")
    player_stats = game_state.get("player_stats", {})
    player_deck = game_state.get("deck_cards", {}).get("player", [])
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.caption("生命值")
        st.markdown(f"❤️ {player_stats.get('hp', 0)}")
    with col2:
        st.caption("能量")
        st.markdown(f"⚡ {player_stats.get('energy', 0)}")
    with col3:
        st.caption("护甲")
        st.markdown(f"🛡️ {player_stats.get('armor', 0)}")
    with col4:
        st.caption("牌堆")
        st.markdown(f"🎴 {len(player_deck)}")

def render_game_controls():
    """渲染游戏控制区域"""
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("结束回合", key="end_turn_button"):
            st.session_state.game_manager.end_turn()
            st.rerun()
    
    with col2:
        # 这里可以添加其他控制按钮
        pass

def render_chat_view():
    """渲染聊天界面"""
    st.header("💬 对话")
    
    # 渲染聊天消息（在任何回合都显示）
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # 获取当前回合状态
    current_turn = st.session_state.game_manager.game_state["turn_info"]["active_player"]
    
    if current_turn == "player":
        # 玩家回合界面
        st.markdown("### 🎮 你的回合")
        
        # 处理玩家回合状态
        if not st.session_state.game_manager._process_player_turn():
            # 只有在action阶段才显示交互界面
            player_turn_state = st.session_state.game_manager.game_state.get("player_turn_state")
            if player_turn_state == "action":
                # 玩家手牌和操作区
                available_cards = st.session_state.game_manager.get_available_cards()
                
                # 卡牌选择
                selected_card_name = st.selectbox(
                    "选择卡牌",
                    options=[card['name'] for card in available_cards],
                    format_func=lambda x: next((f"{card['name']} - {card['type']} (费用:{card.get('cost', 0)})" 
                                          for card in available_cards if card['name'] == x), x),
                    key="card_select"
                )
                
                # 用户输入区域
                user_input = st.chat_input("输入你的行动或问题...", key="chat_input")
                if user_input:
                    add_user_message(user_input)
                    process_user_input_ai(user_input)
                
                # 创建按钮列
                button_cols = st.columns(3)
                
                # 添加快捷操作按钮
                with button_cols[0]:
                    if st.button("使用卡牌", key="use_card", use_container_width=True):
                        message = f"我要使用{selected_card_name}卡牌"
                        add_user_message(message)
                        process_user_input(message)
                        st.rerun()
                        
                with button_cols[1]:
                    if st.button("给出建议", key="get_advice", use_container_width=True):
                        message = f"请分析当前局势，并给出使用{selected_card_name}的建议"
                        add_user_message(message)
                        process_user_input(message)
                        
                with button_cols[2]:
                    if st.button("结束回合", key="end_turn", use_container_width=True):
                        message = "我要结束当前回合"
                        add_user_message(message)
                        st.session_state.game_manager.game_state["player_turn_state"] = "end_turn"
                        st.session_state.game_manager.end_turn()
                        st.rerun()
                
                # 获取选中卡牌的详细信息并显示在按钮下方
                selected_card = next((card for card in available_cards if card['name'] == selected_card_name), None)
                if selected_card:
                    with st.container():
                        card_info = (f"🎴 {selected_card['name']} | "
                                   f"类型: {selected_card['type']} | "
                                   f"费用: {selected_card.get('cost', 0)} | "
                                   f"攻击: {selected_card.get('attack', 0)} | "
                                   f"生命: {selected_card.get('health', 0)} | "
                                   f"效果: {selected_card.get('effect', '无')}")
                        st.text(card_info)
            else:
                st.rerun()
    
    else:
        # 对手回合界面
        st.markdown("### 🤖 对手回合")
        
        # 处理对手回合
        st.session_state.game_manager._process_opponent_turn()

def add_user_message(message):
    """添加用户消息"""
    st.session_state.messages.append({"role": "user", "content": message})

def add_assistant_message(message):
    """添加助手消息"""
    st.session_state.messages.append({"role": "assistant", "content": message})

def main():
    """主函数"""
    # 设置页面配置
    st.set_page_config(
        page_title="🎮 AI卡牌游戏",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 分割界面为游戏区和聊天区
    game_col, chat_col = st.columns([1, 1])
    
    # 渲染游戏区
    with game_col:
        render_game_view()
    
    # 渲染聊天区
    with chat_col:
        render_chat_view()

if __name__ == "__main__":
    main()