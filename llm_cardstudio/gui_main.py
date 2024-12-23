import re
from turtle import up
import streamlit as st
from llm_interaction import LLMInteraction
from game_manager import GameManager
from player_manager import PlayerManager
from debug_utils import debug_utils
import os
import json
import time
from datetime import datetime
from typing import List, Dict

# 初始化全局session state
if 'initialized' not in st.session_state:
    st.session_state.game_manager = GameManager()
    st.session_state.llm_interaction = LLMInteraction()
    st.session_state.player_manager = PlayerManager()
    st.session_state.messages = [{"role": "assistant", "content": "准备好战斗了吗？"}]
    st.session_state.initialized = True
    st.session_state.ai_input = ""


def update_ui_state(show_success_message=None):
    """更新界面状态
    Args:
        show_success_message (str, optional): 如果提供，显示成功消息
    """
    # if show_success_message:
    #     st.success(show_success_message)
    st.rerun()

# def render_command_progress():
#     """渲染命令执行进度"""
#     if st.session_state.game_manager.is_executing_commands():

#         return True
    
#     return False

def process_game_loop():
    """处理游戏循环"""
    game_manager = st.session_state.game_manager
    require_update = False
    
    # 检查是否有命令正在执行
    if game_manager.is_executing_commands():
        current, total = st.session_state.game_manager.get_current_command_progress()
        progress_text = f"执行命令 {current}/{total}"
        st.progress(current / total, text=progress_text)
        # 执行下一个命令
        success = game_manager.process_next_command()
        require_update = True
        # update_ui_state()
    
    # 检查是否有LLM响应
    if st.session_state.ai_input:
        process_user_input_ai(st.session_state.ai_input)
        st.session_state.ai_input = ""
        require_update = True

    # if game_manager.check_game_over():
    #     st.session_state.game_over = True
    
    return require_update

def process_user_input_ai(message):
    """AI处理用户输入"""
    # 获取当前游戏状态
    game_state = st.session_state.game_manager.get_game_state()
    
    # 记录调试信息
    debug_utils.log("llm", "处理用户输入", {
        "用户输入": message
        # "游戏状态": game_state
    })
    
    # 显示运行状态
    status_container = st.container()
    with status_container:
        with st.status("AI思考中...", state="running", expanded=False) as status:
            # 生成AI响应
            ai_response = st.session_state.llm_interaction.generate_ai_response(message, game_state)
            status.update(label="完成", state="complete")
    
    # print(ai_response)
    # 添加AI响应到消息历史
    st.session_state.messages.append({"role": "assistant", "content": ai_response.content})
    
    # 记录调试信息
    debug_utils.log("llm", "AI响应", {"响应内容": ai_response.content})
    # st.rerun()
    # update_ui_state()

def process_user_input(user_input):
    """处理用户输入"""
    with st.spinner("处理中..."):

        add_user_message(user_input)
        # 解析用户输入
        action_result = st.session_state.llm_interaction.parse_user_action(user_input)
        
        # 如果是使用卡牌的操作，将卡牌从手牌移到场上
        if "使用" in user_input and "卡牌" in user_input:
            selected_card_id = st.session_state.get("card_select")
            if selected_card_id:
                debug_utils.log("card", "选中使用卡牌", {
                    "selected_card_id": selected_card_id
                })
                
                # 使用卡牌（会自动处理命令）
                result = st.session_state.game_manager.play_card(str(selected_card_id))
                return
    
        # 如果是攻击的操作，进行攻击
        elif "攻击" in user_input:
            # 进行攻击
            game_over = st.session_state.game_manager.perform_attack("player")
            if game_over:
                # 如果检查到游戏结束，则直接回合结束
                st.session_state.game_manager.game_state["player_turn_state"] = "end_turn"
            return
    
        # 如果是结束回合的操作，直接结束回合
        elif "结束" in user_input and "回合" in user_input:
            st.session_state.game_manager.game_state["player_turn_state"] = "end_turn"
            return

    # 如果用户输入不是使用卡牌的操作，则直接更新UI状态
    # process_message = user_input
    # update_ui_state()

def render_game_view():
    """渲染游戏画面"""
    # process_game_loop()
    # render_command_progress()
    
    st.header("🎮 卡牌战场", divider="rainbow")
    
    # 获取游戏状态
    game_state = st.session_state.game_manager.get_game_state()
    gameloop_state = game_state.get("gameloop_state", "welcome")
    
    # 在侧边栏添加状态显示和更新按钮
    with st.sidebar:
        st.header("🛠️ 游戏控制台")
        
        # 添加保存和载入游戏按钮
        if gameloop_state != "welcome":
            # 保存游戏
            save_name = datetime.now().strftime("save_%Y%m%d-%H%M")
            st.write(f"存档名称: {save_name}")

            if st.button("💾 保存游戏", use_container_width=True):
                success, message = st.session_state.game_manager.save_game(save_name)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # 载入游戏功能仅在welcome状态可用
        if gameloop_state == "welcome":
            save_files = st.session_state.game_manager.get_save_files()
            if save_files:
                selected_save = st.selectbox(
                    "选择存档",
                    options=save_files,
                    format_func=lambda x: f"存档: {x}",
                    key="load_save"
                )
                if st.button("📂 载入游戏", use_container_width=True):
                    success, message = st.session_state.game_manager.load_game(selected_save)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        if st.button("手动更新界面"):
            update_ui_state("手动更新界面")
            
        # 使用expander显示游戏状态
        with st.expander("🔍 查看游戏状态", expanded=True):
            st.json(game_state)
    
    # 根据游戏状态渲染不同界面
    game_state_display = gameloop_state
    if gameloop_state == "player_turn":
        player_turn_state = st.session_state.game_manager.game_state.get("player_turn_state", "")
        game_state_display = f"{gameloop_state} ({player_turn_state})"
    elif gameloop_state == "opponent_turn":
        opponent_turn_state = st.session_state.game_manager.game_state.get("opponent_turn_state", "")
        game_state_display = f"{gameloop_state} ({opponent_turn_state})"
    
    st.caption(f"当前游戏状态: {game_state_display}")
    
    if gameloop_state == "welcome":
        st.markdown("### 👋 欢迎来到卡牌游戏！")
        
        # 获取当前文件所在目录的路径
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 构建完整的文件路径
        decks_json_path = os.path.join(current_dir, 'decks.json')

        # 使用完整路径打开文件
        with open(decks_json_path, 'r', encoding='utf-8') as f:
            decks_data = json.load(f)
        
        # 创建卡组选择列
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎮 选择你的卡组")
            player_deck = st.selectbox(
                "我方卡组",
                options=list(decks_data.keys()),
                format_func=lambda x: f"{decks_data[x]['name']} - {decks_data[x]['description']}",
                key="player_deck_select"
            )
            
            # 显示选中卡组的详细信息
            if player_deck:
                # with st.expander("查看卡组详情", expanded=True):
                with st.container(height=300):
                    st.write(f"**卡组名称:** {decks_data[player_deck]['name']}")
                    st.write(f"**卡组描述:** {decks_data[player_deck]['description']}")
                    st.write("**卡牌列表:**")
                    # 读取cards.json获取卡牌详细信息
                    cards_json_path = os.path.join(current_dir, 'cards.json')
                    with open(cards_json_path, 'r', encoding='utf-8') as f:
                        cards_data = json.load(f)
                    cards_dict = {card['id']: card for card in cards_data}
                    for card_id in decks_data[player_deck]['cards']:
                        if card_id in cards_dict:
                            card = cards_dict[card_id]
                            st.write(f"- {card['name']} ({card['type']}, 费用:{card['cost']})")
        
        with col2:
            st.markdown("#### 🤖 选择对手卡组")
            opponent_deck = st.selectbox(
                "对手卡组",
                options=list(decks_data.keys()),
                format_func=lambda x: f"{decks_data[x]['name']} - {decks_data[x]['description']}",
                key="opponent_deck_select"
            )
            
            # 显示选中卡组的详细信息
            if opponent_deck:
                # with st.expander("查看卡组详情", expanded=True):
                with st.container(height=300):
                    st.write(f"**卡组名称:** {decks_data[opponent_deck]['name']}")
                    st.write(f"**卡组描述:** {decks_data[opponent_deck]['description']}")
                    st.write("**卡牌列表:**")
                    for card_id in decks_data[opponent_deck]['cards']:
                        if card_id in cards_dict:
                            card = cards_dict[card_id]
                            st.write(f"- {card['name']} ({card['type']}, 费用:{card['cost']})")
        
        # 开始游戏按钮
        if st.button("开始游戏", key="start_game", use_container_width=True):
            # 保存选择的卡组到游戏状态
            st.session_state.game_manager.selected_decks = {
                "player": decks_data[player_deck]['cards'],
                "opponent": decks_data[opponent_deck]['cards']
            }
            st.session_state.game_manager.start_game()
            st.rerun()

        return
    
    # 显示回合息
    st.caption(f"第 {game_state['turn_info']['current_turn']} 回合 - {'我方回合' if game_state['turn_info']['active_player'] == 'player' else '对手回合'}")
    
    # 显示对手状态
    is_opponent_active = game_state["turn_info"]["active_player"] == "opponent"
    opponent_title_color = "yellow" if is_opponent_active else "white"
    st.markdown(f"<h3 style='color: {opponent_title_color};'>🤖 对手状态</h3>", unsafe_allow_html=True)
    
    opponent_stats = game_state.get("opponent_stats", {})
    opponent_deck_count = len(game_state.get("deck_state", {}).get("opponent", {}).get("deck", []))
    opponent_hand = game_state.get("hand_cards", {}).get("opponent", [])
    col1, col2, col3, col4, col5 = st.columns(5)
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
        st.markdown(f"🎴 {opponent_deck_count}")
    with col5:
        st.caption("手牌")
        st.markdown(f"✋ {len(opponent_hand)}")

    # 对手场上卡牌
    st.markdown("#### 🎯 对手场上卡牌")
    opponent_field_cards = game_state.get("field_cards", {}).get("opponent", [])
    if not opponent_field_cards:
        st.caption("对手场上暂无卡牌")
    else:
        cols = st.columns(len(opponent_field_cards), border=True)
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
        cols = st.columns(len(player_field_cards), border=True)
        for idx, card in enumerate(player_field_cards):
            with cols[idx]:
                st.markdown(f"""
                    **{card.get('name', '未知卡牌')}**  
                    *{card.get('type', '未知类型')}*  
                    效果: {card.get('effect', '无')}  
                    状态: {card.get('status', '未知状态')}
                """)
    
    # 显示玩家状态
    is_player_active = game_state["turn_info"]["active_player"] == "player"
    player_title_color = "yellow" if is_player_active else "white"
    st.markdown(f"<h3 style='color: {player_title_color};'>👤 我方状态</h3>", unsafe_allow_html=True)
    
    player_stats = game_state.get("player_stats", {})
    player_deck_count = len(game_state.get("deck_state", {}).get("player", {}).get("deck", []))
    player_hand = game_state.get("hand_cards", {}).get("player", [])
    col1, col2, col3, col4, col5 = st.columns(5)
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
        st.markdown(f"🎴 {player_deck_count}")
    with col5:
        st.caption("手牌")
        st.markdown(f"✋ {len(player_hand)}")

    # # 渲染游戏附加控制区域
    # render_sub_controls(gameloop_state)


def render_sub_controls(gameloop_state):
    """渲染游戏附加控制区域"""
    game_manager = st.session_state.game_manager
    return    


def render_chat_view_game_controls():
    """渲染聊天界面"""
    st.header("💬 LLM Card Studio")
    
    # 获取游戏状态
    game_state = st.session_state.game_manager.get_game_state()
    gameloop_state = game_state.get("gameloop_state", "welcome")
    
    # 渲聊天消息（在任何回合都显示）
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # render command progress 渲染命令执行进度
    # render AI in progress 渲染AI执行进度
    if process_game_loop():
        # 如果有进行渲染, 则更新画面
        update_ui_state()
        return

    # 在欢迎界面和玩家回合的action阶段显示交互界面
    if gameloop_state == "welcome":
        # 欢迎界面对话
        user_input = st.chat_input("你可以问我任何关于游戏的问题...", key="welcome_chat_input")
        if user_input:
            add_user_input_ai(user_input)
            update_ui_state()
            return
    
    elif gameloop_state == "player_turn":
        # 玩家回合界面
        st.markdown("### 🎮 你的回合")
        
        # 有在action阶段才显示交互界面
        player_turn_state = game_state.get("player_turn_state")
        if player_turn_state == "action":
            # 玩家手牌和操作区
            available_cards = st.session_state.game_manager.get_available_cards()
            # 按费用排序卡牌
            sorted_cards = sorted(available_cards, key=lambda card: card.get('cost', 0))
            
            # 卡牌选择
            selected_card_id = st.selectbox(
                "选择卡牌",
                options=[str(card['id']) for card in sorted_cards],
                format_func=lambda x: next((f"{card['name']} - {card['type']} (费用:{card.get('cost', 0)})" 
                                      for card in sorted_cards if str(card['id']) == x), x),
                key="card_select"
            )
            
            # 用户输入区域
            user_input = st.chat_input("输入你的行动或问题...", key="chat_input")
            if user_input:
                # add_user_message(user_input)
                # process_user_input_ai(user_input)
                add_user_input_ai(user_input)
                update_ui_state()
                return

            # 创建按钮列
            button_cols = st.columns(4)  # 改为4列以容纳攻击按钮
            
            # 添加快捷操作钮
            with button_cols[0]:
                if st.button("使用卡牌", key="use_card", use_container_width=True):
                    card = next((card for card in sorted_cards if str(card['id']) == selected_card_id), None)
                    if card:
                        message = f"我使用{card['name']}卡牌"
                    # add_user_message(message)
                    process_user_input(message)
                    update_ui_state()
                    return
                    
            with button_cols[1]:
                # 检查是否已经攻击过和是否是第一回合
                # 初始化session state用于控制选择框的显示
                if 'show_attack_options' not in st.session_state:
                    st.session_state.show_attack_options = False
                has_attacked = st.session_state.game_manager.game_state.get("has_attacked_this_turn", False)
                is_first_turn = st.session_state.game_manager.game_state["turn_info"]["current_turn"] == 1
                attack_disabled = has_attacked or is_first_turn
                
                attack_button_text = "⚔️ 攻击"
                if has_attacked:
                    attack_button_text = "⚔️ 已攻击"
                elif is_first_turn:
                    attack_button_text = "⚔️ 第一回合禁止攻击"
                
                game_manager = st.session_state.game_manager
                player_field = game_manager.game_state["field_cards"]["player"]
                opponent_field = game_manager.game_state["field_cards"]["opponent"]

                if st.button(attack_button_text, key="attack", use_container_width=True, disabled=attack_disabled):
                    message = "我要攻击对手"
                    # add_user_message(message)
                    # process_user_input(message)
                    st.session_state.show_attack_options = True
                    
            with button_cols[2]:
                if st.button("给出建议", key="get_advice", use_container_width=True):
                    card = next((card for card in sorted_cards if str(card['id']) == selected_card_id), None)
                    if card:
                        message = f"分析当前局势，并给出使用{card['name']}的建议"
                    # add_user_message(message)
                    # process_user_input_ai(message)
                    add_user_input_ai(message)
                    update_ui_state()
                    return
                   
            with button_cols[3]:
                if st.button("结束回合", key="end_turn", use_container_width=True):
                    message = "我要结束当前回合"
                    # st.session_state.game_manager.game_state["player_turn_state"] = "end_turn"
                    # add_user_message(message)
                    process_user_input(message)
                    update_ui_state()
                    # st.session_state.game_manager._process_gameloop_state()
                    return

            # 附加指令区
            if st.session_state.show_attack_options:
                # 创建攻击者选择框
                attacker_options = [f"{card['name']} (ID: {card['id']})" for card in player_field]
                if attacker_options:
                    selected_attacker = st.selectbox("选择攻击者", attacker_options, key="attacker_select")
                    attacker_id = selected_attacker.split("ID: ")[1][:-1] if selected_attacker else None
                    
                    # 创建防御者选择框
                    defender_options = ["直接攻击对手"] + [f"{card['name']} (ID: {card['id']})" for card in opponent_field]
                    selected_defender = st.selectbox("选择攻击目标", defender_options, key="defender_select")
                    
                    if st.button("确认攻击", disabled=not selected_attacker):
                        if selected_defender == "直接攻击对手":
                            game_manager.perform_attack(attacker_id)
                        else:
                            defender_id = selected_defender.split("ID: ")[1][:-1]
                            game_manager.perform_attack(attacker_id, defender_id)
                        st.session_state.show_attack_options = False    
                        update_ui_state()
                        return

            # 特别说明：进入process_user_input() 如果用户输入不是使用卡牌的操作，则直接更新UI状态
            # process_user_input( user_input )
            #   process_message = user_input
            #   update_ui_state()

            # 获取选中卡牌的详细信息并显示在按钮下方
            selected_card = next((card for card in sorted_cards if str(card['id']) == selected_card_id), None)
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
            # 非action阶段，直接自动执行状态
            st.session_state.game_manager._process_gameloop_state()
    
    elif gameloop_state == "opponent_turn":
        # 对手回合界面
        st.markdown("### 🤖 对手回合")
        st.session_state.game_manager._process_gameloop_state()

    # 处理自动过渡一个状态        
    last_state = st.session_state.get("last_gameloop_state", None)
    if (gameloop_state != "welcome" and 
        gameloop_state != "player_turn" and 
        gameloop_state != "opponent_turn"):
        
        if gameloop_state == last_state:
            debug_utils.log("state", "！！！状态重复", {
                "当前状态": gameloop_state,
                "上次状态": last_state,
                "玩家回合状态": st.session_state.game_manager.game_state.get("player_turn_state"),
                "对手回合状态": st.session_state.game_manager.game_state.get("opponent_turn_state")
            })
        else:
            # 处理状态
            st.session_state["last_gameloop_state"] = gameloop_state
            st.session_state.game_manager._process_gameloop_state()
            # 刷新UI + st.rerun()
            # update_ui_state()
            # st.rerun()
    
    # 记录当前状态
    st.session_state["last_gameloop_state"] = gameloop_state

def add_user_message(message):
    """添加用户消息"""
    st.session_state.messages.append({"role": "user", "content": message})

def add_assistant_message(message):
    """添加助手消息"""
    st.session_state.messages.append({"role": "assistant", "content": message})

def add_user_input_ai(message):
    """添加用户输入AI"""
    add_user_message(message)
    st.session_state.ai_input = message


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
    
    # 渲染聊天区与游戏控制区
    with chat_col:
        render_chat_view_game_controls()

if __name__ == "__main__":
    main()