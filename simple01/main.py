import streamlit as st
from llm_interaction import LLMInteraction
from game_manager import GameManager
from player_manager import PlayerManager

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

def process_user_input(user_input):
    """处理用户输入"""
    with st.spinner("处理中..."):
        # 解析用户输入
        action_result = st.session_state.llm_interaction.parse_user_action(user_input)
        
        # 如果是使用卡牌的操作，将卡牌从手牌移到场上
        if "使用" in user_input and "卡牌" in user_input:
            selected_card = st.session_state.get("card_select")
            if selected_card:
                print("选中的卡牌:", selected_card)
                
                # 使用卡牌
                result = st.session_state.game_manager.play_card(selected_card)
                if isinstance(result, dict) and result.get("removed_cards"):
                    # 简化移除卡牌的显示
                    removed_names = [card['name'] for card in result["removed_cards"]]
                    print("移除的卡牌:", ", ".join(removed_names))
                
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
    st.header("🎮 卡牌战场")
    
    # 直接从game_manager获取状态
    game_state = st.session_state.game_manager.get_game_state()
    
    # 在侧边栏添加状态显示和更新按钮
    with st.sidebar:
        st.header("🛠️ 游戏控制台")
        if st.button("手动更新界面"):
            update_ui_state("手动更新界面")
            
        # 使用expander显示游戏状态
        with st.expander("🔍 查看游戏状态", expanded=True):
            st.json(game_state)
    
    # 显示玩家状态
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("❤️ 生命", game_state.get("player_stats", {}).get("hp", 0))
    with col2:
        st.metric("⚡ 能量", game_state.get("player_stats", {}).get("energy", 0))
    with col3:
        st.metric("🛡️ 护甲", game_state.get("player_stats", {}).get("armor", 0))
    
    # 回合信息
    with st.container():
        turn_info = game_state.get("turn_info", {})
        st.info(f"第 {turn_info.get('current_turn', 1)} 回合")
    
    # 场上卡牌区域
    st.subheader("🎯 场上卡牌")
    field_cards = game_state.get("field_cards", [])
    
    if not field_cards:
        st.info("场上暂无卡牌")
    else:
        # 使用列布局显示场上卡牌
        cols = st.columns(len(field_cards))
        for idx, card in enumerate(field_cards):
            with cols[idx]:
                st.markdown(f"""
                    **{card['name']}**  
                    效果: {card['effect']}  
                    状态: {card['status']}
                """)

def render_chat_view():
    """渲染聊天界面"""
    st.header("💬 对话")
    
    # 玩家手牌和操作区
    available_cards = st.session_state.game_manager.get_available_cards()
    # 简化手牌显示
    card_names = [card['name'] for card in available_cards]
    print("可用卡牌:", ", ".join(card_names))
    
    # 卡牌选择和操作按钮放在同一行
    selected_card = st.selectbox(
        "选择卡牌",
        options=[card['name'] for card in available_cards],
        format_func=lambda x: next((f"{card['name']} - {card['type']} (消耗:{card.get('mana_cost', 0)})" 
                                  for card in available_cards if card['name'] == x), x),
        key="card_select"
    )
    
    # 用户输入区域
    user_input = st.chat_input("输入你的行动或问题...", key="chat_input")
    if user_input:
        add_user_message(user_input)
        process_user_input(user_input)
    
    # 操作按钮
    button_cols = st.columns(3)
    with button_cols[0]:
        if st.button("使用卡牌", key="use_card", use_container_width=True):
            message = f"我要使用{selected_card}卡牌"
            add_user_message(message)
            process_user_input(message)
    with button_cols[1]:
        if st.button("分析建议", key="analyze_card", use_container_width=True):
            message = f"请分析当前局势，并给出使用{selected_card}的建议"
            add_user_message(message)
            #process_user_input(message)
    with button_cols[2]:
        if st.button("结束回合", key="end_turn", use_container_width=True):
            message = "我要结束当前回合"
            add_user_message(message)
            #process_user_input(message)
    
    # 渲染聊天消息
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


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