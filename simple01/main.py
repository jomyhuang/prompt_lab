import streamlit as st
from llm_interaction import LLMInteraction
from game_manager import GameManager
from player_manager import PlayerManager

def init_session_state():
    """初始化session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]

    if "game_state" not in st.session_state:
        st.session_state.game_state = {}

def render_game_view(game_manager):
    """渲染游戏画面"""
    st.header("🎮 卡牌战场")
    
    # 获取游戏状态
    game_state = game_manager.get_game_state()
    
    # 玩家状态区域
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("❤️ 生命", game_state.get("player_stats", {}).get("hp", 0))
    with col2:
        st.metric("⚡ 能量", game_state.get("player_stats", {}).get("energy", 0))
    with col3:
        st.metric("🛡️ 护甲", game_state.get("player_stats", {}).get("armor", 0))
    
    # 回合信息
    with st.container():
        st.subheader("🎯 当前回合")
        turn_info = game_state.get("turn_info", {})
        st.info(f"第 {turn_info.get('current_turn', 1)} 回合")
    
    # 场上卡牌区域
    st.subheader("🎯 场上卡牌")
    field_cards = game_manager.get_field_cards()
    
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
                """, unsafe_allow_html=True)

def render_chat_view(game_manager):
    """渲染对话界面"""
    st.title("💬 LLM Card Studo")
    st.caption("🚀 A Streamlit chatbot powered by Langchain")

    # 玩家手牌和操作区
    available_cards = game_manager.get_available_cards()
    
    # 卡牌选择和操作按钮放在同一行
    selected_card = st.selectbox(
        "选择卡牌",
        options=available_cards,
        format_func=lambda x: f"{x['name']} - {x['type']} (消耗:{x.get('mana_cost', 0)})",
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
            message = f"我要使用{selected_card['name']}卡牌"
            add_user_message(message)
            process_user_input(message)
    with button_cols[1]:
        if st.button("询问建议", key="ask_advice", use_container_width=True):
            message = f"请分析当前局势，并给出使用{selected_card['name']}的建议"
            add_user_message(message)
            #process_user_input(message)
    with button_cols[2]:
        if st.button("结束回合", key="end_turn", use_container_width=True):
            message = "我要结束当前回合"
            add_user_message(message)
            #process_user_input(message)
    
    chat_container = st.container(height=600)
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

def process_user_input(user_input):
    """处理用户输入"""
    with st.spinner("处理中..."):
        # 解析用户输入
        action_result = llm_interaction.parse_user_action(user_input)
        
        # 如果是使用卡牌的操作，将卡牌从手牌移到场上
        if "使用" in user_input and "卡牌" in user_input:
            selected_card = st.session_state.get("card_select")
            if selected_card:
                st.write("选中的卡牌:", selected_card)  # 调试信息
                
                # 使用卡牌
                result = game_manager.play_card(selected_card['name'])
                st.write("使用卡牌结果:", result)  # 调试信息
                
                if isinstance(result, dict) and result.get("status") == "success":
                    st.success(f"成功使用卡牌：{selected_card['name']}")
                    if result.get("message"):
                        st.info(result["message"])
                    
                    # 显示场上卡牌状态
                    field_cards = game_manager.get_field_cards()
                    st.write("场上卡牌:", field_cards)  # 调试信息
                    
                    # 强制刷新界面
                    st.rerun()
                else:
                    # 显示错误信息
                    st.error(result if isinstance(result, str) else "使用卡牌失败")
        
        # 更新游戏状态
        game_state = game_manager.update_game_state(action_result)
        st.write("当前游戏状态:", game_state)  # 调试信息
        
        # 暂时关闭AI响应
        # ai_response = llm_interaction.generate_ai_response(game_state)
        # add_assistant_message(ai_response)

def main():
    # 设置页面配置
    st.set_page_config(
        page_title="🎮 AI卡牌游戏",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
  
    # 初始化session state和管理器
    init_session_state()
    global llm_interaction, game_manager, player_manager
    llm_interaction = LLMInteraction()
    game_manager = GameManager()
    player_manager = PlayerManager()
    
    # 创建左右两列布局
    game_col, chat_col = st.columns(2)
    
    # 左侧游戏画面
    with game_col:
        render_game_view(game_manager)
    
    # 右侧对话区域
    with chat_col:
        render_chat_view(game_manager)

if __name__ == "__main__":
    main()