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
import asyncio

# 初始化全局session state
if 'initialized' not in st.session_state:
    st.session_state.game_manager = GameManager()
    st.session_state.llm_interaction = LLMInteraction()
    st.session_state.player_manager = PlayerManager()
    st.session_state.messages = [{"role": "assistant", "content": "准备好战斗了吗？"}]
    st.session_state.initialized = True
    st.session_state.ai_input = ""
    # 初始化卡牌选择状态
    st.session_state.card_selection = {
        "is_selecting": False,  # 是否处于选择状态
        "action_type": None,    # 动作类型 (attack/play/etc)
        "source_type": None,    # 来源类型 (hand/field)
        "target_type": None,    # 目标类型 (opponent_field/opponent_hero)
        "selected_card": None,  # 已选择的卡牌
        "target_card": None,    # 已选择的目标
        "callback": None        # 选择完成后的回调函数
    }

def update_ui_state(show_success_message=None):
    """更新界面状态
    Args:
        show_success_message (str, optional): 如果提供，显示成功消息
    """
    st.rerun()
    # st.experimental_rerun()

def render_sidebar_controls(game_state, gameloop_state):
    """渲染侧边栏控制界面"""
    with st.sidebar:
        st.header("🛠️ 游戏控制台")
        
        # 添加保存和载入游戏按钮
        if gameloop_state != "welcome":
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

def render_deck_selection():
    """渲染卡组选择界面"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    decks_json_path = os.path.join(current_dir, 'decks.json')
    cards_json_path = os.path.join(current_dir, 'cards.json')

    with open(decks_json_path, 'r', encoding='utf-8') as f:
        decks_data = json.load(f)
    with open(cards_json_path, 'r', encoding='utf-8') as f:
        cards_data = json.load(f)
    
    cards_dict = {card['id']: card for card in cards_data}
    col1, col2 = st.columns(2)
    
    # 渲染玩家卡组选择
    with col1:
        st.markdown("#### 🎮 选择你的卡组")
        player_deck = st.selectbox(
            "我方卡组",
            options=list(decks_data.keys()),
            format_func=lambda x: f"{decks_data[x]['name']} - {decks_data[x]['description']}",
            key="player_deck_select"
        )
        
        if player_deck:
            with st.container(height=300):
                st.write(f"**卡组名称:** {decks_data[player_deck]['name']}")
                st.write(f"**卡组描述:** {decks_data[player_deck]['description']}")
                st.write("**卡牌列表:**")
                for card_id in decks_data[player_deck]['cards']:
                    if card_id in cards_dict:
                        card = cards_dict[card_id]
                        st.write(f"- {card['name']} ({card['type']}, 费用:{card['cost']})")
    
    # 渲染对手卡组选择
    with col2:
        st.markdown("#### 🤖 选择对手卡组")
        opponent_deck = st.selectbox(
            "对手卡组",
            options=list(decks_data.keys()),
            format_func=lambda x: f"{decks_data[x]['name']} - {decks_data[x]['description']}",
            key="opponent_deck_select"
        )
        
        if opponent_deck:
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
        st.session_state.game_manager.selected_decks = {
            "player": decks_data[player_deck]['cards'],
            "opponent": decks_data[opponent_deck]['cards']
        }
        process_user_input("开始游戏")
        return

def render_game_stats(game_state):
    """渲染游戏状态信息"""
    opponent_stats = game_state.get("opponent_stats", {})
    opponent_deck_count = len(game_state.get("deck_state", {}).get("opponent", {}).get("deck", []))
    opponent_hand = game_state.get("hand_cards", {}).get("opponent", [])
    
    is_opponent_active = game_state["turn_info"]["active_player"] == "opponent"
    opponent_title_color = "yellow" if is_opponent_active else "white"
    st.markdown(f"<h3 style='color: {opponent_title_color};'>🤖 对手状态</h3>", unsafe_allow_html=True)
    
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

def render_opponent_field(game_state):
    """渲染对手场上卡牌"""
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

def render_player_field(game_state):
    """渲染玩家场上卡牌"""
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

def render_game_view():
    """渲染游戏画面"""
    st.header("🎮 LLM Card Studio", divider="rainbow")
    
    # 获取游戏状态
    game_state = st.session_state.game_manager.get_game_state()
    gameloop_state = game_state.get("gameloop_state", "welcome")
    
    # 渲染侧边栏控制
    render_sidebar_controls(game_state, gameloop_state)
    
    # 根据游戏状态渲染不同界面
    game_state_display = gameloop_state
    if gameloop_state == "player_turn":
        player_turn_state = st.session_state.game_manager.game_state.get("player_turn_state", "")
        game_state_display = f"{gameloop_state} ({player_turn_state})"
    elif gameloop_state == "opponent_turn":
        opponent_turn_state = st.session_state.game_manager.game_state.get("opponent_turn_state", "")
        game_state_display = f"{gameloop_state} ({opponent_turn_state})"
    
    st.caption(f"当前游戏状态: {game_state_display}")
    
    # 欢迎界面
    if gameloop_state == "welcome":
        st.markdown("### 👋 欢迎来到卡牌游戏！")
        render_deck_selection()
        return
    
    # 显示回合信息
    st.caption(f"第 {game_state['turn_info']['current_turn']} 回合 - {'我方回合' if game_state['turn_info']['active_player'] == 'player' else '对手回合'}")
    
    # 渲染游戏状态
    render_game_stats(game_state)
    
    # 渲染场上卡牌
    render_opponent_field(game_state)
    st.divider()
    render_player_field(game_state)
    
    # 渲染玩家状态
    player_stats = game_state.get("player_stats", {})
    is_player_active = game_state["turn_info"]["active_player"] == "player"
    player_title_color = "yellow" if is_player_active else "white"
    st.markdown(f"<h3 style='color: {player_title_color};'>👤 我方状态</h3>", unsafe_allow_html=True)
    
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

async def _process_user_input_ai(user_input):
    """AI处理用户输入"""
    # 获取当前游戏状态
    game_state = st.session_state.game_manager.get_game_state()
    
    # 记录调试信息
    # debug_utils.log("llm", "处理用户输入", { 注意这里我注释了，防止引用错误
    #     "用户输入": message
    # })
    
    # 显示运行状态
    status_container = st.container()
    with status_container:
        with st.status("AI响应...", state="running", expanded=False) as status:
            action_result = st.session_state.llm_interaction.parse_user_action(user_input)
            ai_message = await st.session_state.llm_interaction.generate_ai_response(user_input, game_state)

            status.update(label="AI响应完成", state="complete", expanded=False)
            st.session_state.messages.append({"role": "assistant", "content": ai_message.content})

def process_user_input(user_input):
    """处理用户输入"""
    with st.spinner("处理中..."):
        add_user_message(user_input)
        # 解析用户输入
        action_result = st.session_state.llm_interaction.parse_user_action(user_input)
        game_state = st.session_state.game_manager.get_game_state()
        
        # 如果是开始游戏的操作
        if game_state["gameloop_state"] == "welcome" and "开始" in user_input and "游戏" in user_input:
            st.session_state.game_manager.start_game()
            return
        
        # 如果是使用卡牌的操作，将卡牌从手牌移到场上
        elif "使用" in user_input and "卡牌" in user_input:
            selected_card_id = st.session_state.get("card_select")
            if selected_card_id:
                debug_utils.log("card", "选中使用卡牌", {
                    "selected_card_id": selected_card_id
                })
                
                # 使用卡牌（会自动处理命令）
                result = st.session_state.game_manager.play_card(str(selected_card_id))
            return
    
        # 如果是攻击的操作
        elif "攻击" in user_input:
            if st.session_state.card_selection["is_selecting"]:
                selected_card = st.session_state.card_selection["selected_card"]
                target_card = st.session_state.card_selection["target_card"]
                if selected_card:
                    target_id = target_card["id"] if isinstance(target_card, dict) else target_card
                    # success_attack = asyncio.run( st.session_state.game_manager.async_perform_attack(
                    #     attacker_card_id=selected_card["id"],
                    #     target_card_id=target_id,
                    #     player_type="player"
                    # ) )
                    success_attack = st.session_state.game_manager.perform_attack(
                        attacker_card_id=selected_card["id"],
                        target_card_id=target_id,
                        player_type="player"
                    )
                end_card_selection()
            else:
                start_card_selection("attack", "field", "opponent_field")
            return
    
        # 如果是结束回合的操作，直接结束回合
        elif "结束" in user_input and "回合" in user_input:
            st.session_state.game_manager.game_state["player_turn_state"] = "end_turn"
            st.session_state.game_manager._process_gameloop_state()
            return

        # 不理解用户输入
        else:
            add_assistant_message("无法处理用户输入")
            debug_utils.log("game", "无法处理用户输入", {
                "用户输入": user_input
            })
        

def render_action_controls():
    """渲染玩家行动控制界面"""
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
        add_user_input_ai(user_input)
        # update_ui_state()
        return

    # 创建按钮列
    button_cols = st.columns(4)
    
    # 使用卡牌按钮
    with button_cols[0]:
        if st.button("使用卡牌", key="use_card", use_container_width=True):
            card = next((card for card in sorted_cards if str(card['id']) == selected_card_id), None)
            if card:
                message = f"我使用{card['name']}卡牌"
                process_user_input(message)
                # update_ui_state()
                return
    
    # 攻击按钮
    with button_cols[1]:
        has_attacked = st.session_state.game_manager.game_state.get("has_attacked_this_turn", False)
        is_first_turn = st.session_state.game_manager.game_state["turn_info"]["current_turn"] == 1
        attack_disabled = has_attacked or is_first_turn
        
        attack_button_text = "⚔️ 攻击"
        if has_attacked:
            attack_button_text = "⚔️ 已攻击"
        elif is_first_turn:
            attack_button_text = "⚔️ 第一回合禁止攻击"
        
        if st.button(attack_button_text, key="attack", use_container_width=True, disabled=attack_disabled):
            start_card_selection("attack", "field", "opponent_field")
            # update_ui_state()
            return
    
    # 建议按钮        
    with button_cols[2]:
        if st.button("给出建议", key="get_advice", use_container_width=True):
            card = next((card for card in sorted_cards if str(card['id']) == selected_card_id), None)
            if card:
                message = f"分析当前局势，并给出使用{card['name']}的建议"
                add_user_input_ai(message)
                # update_ui_state()
                return
    
    # 结束回合按钮
    with button_cols[3]:
        if st.button("结束回合", key="end_turn", use_container_width=True):
            message = "我要结束当前回合"
            process_user_input(message)
            # update_ui_state()
            return

    # 显示选中卡牌信息
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

def render_chat_view():
    """渲染聊天界面"""
    # 获取游戏状态
    game_state = st.session_state.game_manager.get_game_state()
    gameloop_state = game_state.get("gameloop_state", "welcome")
    
    # 渲染聊天消息历史
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # 渲染对话输入框(在welcome阶段渲染)
    if gameloop_state == "welcome":
        user_input = st.chat_input("输入你的行动或问题...", key="chat_input")
        if user_input:
            add_user_input_ai(user_input)
            # update_ui_state()
            return

def render_action_view():
    """渲染玩家操作界面"""
    game_state = st.session_state.game_manager.get_game_state()
    gameloop_state = game_state.get("gameloop_state", "welcome")

    if gameloop_state == "player_turn":
        # 玩家回合界面
        st.markdown("### 🎮 你的回合")
        
        # 优先处理卡牌选择状态
        # 如果正在选择卡牌,显示选择界面并返回
        if st.session_state.card_selection["is_selecting"]:
            render_card_selection()
            return
            
        # 检查玩家回合状态
        player_turn_state = game_state.get("player_turn_state")
        if player_turn_state == "action":
            # 在action阶段渲染玩家操作界面
            render_action_controls()
        else:
            # 非action阶段，自动处理游戏状态
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

def start_card_selection(action_type, source_type, target_type, callback=None):
    """开始卡牌选择流程
    
    Args:
        action_type: 动作类型 (attack/play/etc)
        source_type: 来源类型 (hand/field)
        target_type: 目标类型 (opponent_field/opponent_hero)
        callback: 选择完成后的回调函数
    """
    st.session_state.card_selection = {
        "is_selecting": True,
        "action_type": action_type,
        "source_type": source_type,
        "target_type": target_type,
        "selected_card": None,
        "target_card": None,
        "callback": callback
    }

    # 更新UI
    update_ui_state()

def end_card_selection():
    """结束卡牌选择流程"""
    if st.session_state.card_selection["callback"]:
        st.session_state.card_selection["callback"](
            st.session_state.card_selection["selected_card"],
            st.session_state.card_selection["target_card"]
        )
    st.session_state.card_selection = {
        "is_selecting": False,
        "action_type": None,
        "source_type": None,
        "target_type": None,
        "selected_card": None,
        "target_card": None,
        "callback": None
    }

    # 更新UI
    update_ui_state()

def render_card_selection():
    """渲染卡牌选择界面"""
    if not st.session_state.card_selection["is_selecting"]:
        return

    game_state = st.session_state.game_manager.get_game_state()
    selection = st.session_state.card_selection

    # 获取来源卡牌列表
    source_cards = []
    if selection["source_type"] == "hand":
        source_cards = game_state.get("hand_cards", {}).get("player", [])
    elif selection["source_type"] == "field":
        source_cards = game_state.get("field_cards", {}).get("player", [])

    # 获取目标卡牌列表
    target_cards = []
    if selection["target_type"] == "opponent_field":
        target_cards = game_state.get("field_cards", {}).get("opponent", [])

    # 渲染来源卡牌选择
    if source_cards:
        source_id = st.selectbox(
            "选择卡牌",
            options=[str(card['id']) for card in source_cards],
            format_func=lambda x: next((f"{card['name']} (攻击力:{card.get('attack', 0)})" 
                                if selection["action_type"] == "attack" 
                                else f"{card['name']} (费用:{card.get('cost', 0)})"
                                for card in source_cards if str(card['id']) == x), x),
            key="source_select"
        )
        selection["selected_card"] = next((card for card in source_cards if str(card['id']) == source_id), None)

    # 渲染目标选择
    if selection["target_type"] == "opponent_field":
        if target_cards:
            target_options = [str(card['id']) for card in target_cards]
            if selection["action_type"] == "attack":
                target_options.append("opponent_hero")
            target_id = st.selectbox(
                "选择目标",
                options=target_options,
                format_func=lambda x: "对手英雄" if x == "opponent_hero" else next((f"{card['name']} (生命值:{card.get('health', 0)})" 
                                            for card in target_cards if str(card['id']) == x), x),
                key="target_select"
            )
            if target_id == "opponent_hero":
                selection["target_card"] = "opponent_hero"
            else:
                selection["target_card"] = next((card for card in target_cards if str(card['id']) == target_id), None)
        elif selection["action_type"] == "attack":
            st.info("对手场上没有卡牌,将直接攻击对手英雄")
            selection["target_card"] = "opponent_hero"

    # 确认按钮
    if st.button("确认", key="confirm_selection", use_container_width=True):
        if selection["selected_card"]:
            if selection["action_type"] == "attack":
                # 构造攻击命令
                attacker_card = selection["selected_card"]
                target_card = selection["target_card"]
                if target_card == "opponent_hero":
                    message = f"我用{attacker_card['name']}攻击对手英雄"
                else:
                    message = f"我用{attacker_card['name']}攻击{target_card['name']}"
                # 处理攻击命令
                process_user_input(message)
            end_card_selection()
            # update_ui_state()
            return

# def _process_game_loop():
#     """处理游戏循环"""
#     game_manager = st.session_state.game_manager
#     require_update = False
    
#     # 检查是否有命令正在执行
#     if game_manager.is_executing_commands():
#         current, total = st.session_state.game_manager.get_current_command_progress()
#         progress_text = f"执行命令 {current}/{total}"
#         st.progress(current / total, text=progress_text)
#         # 执行下一个命令
#         success = game_manager.process_next_command()
#         require_update = True
    
#     # 检查是否有LLM响应
#     if st.session_state.ai_input:
#         _process_user_input_ai(st.session_state.ai_input)
#         st.session_state.ai_input = ""
#         require_update = True
    
#     return require_update

async def _process_game_loop():
    """处理游戏循环"""
    game_manager = st.session_state.game_manager
    require_update = False
    
    # if game_manager.is_executing_commands():
    #     print("enter 命令序列 loop")
    #     require_update = True
    #     while game_manager.is_executing_commands():
    #         update_ui_state()
    #         await asyncio.sleep(0)
    #     print("exit 命令序列 loop")
 
    # 检查是否有命令正在执行
    if game_manager.is_executing_commands():
        current, total = game_manager.get_current_command_progress()
        progress_text = f"执行命令 {current}/{total}"
        st.progress(current / total, text=progress_text)
        # 执行下一个命令
        has_next_command = await game_manager.async_process_next_command()
        require_update = True
 
    # 检查是否有LLM响应
    if st.session_state.ai_input:
        await _process_user_input_ai(st.session_state.ai_input)     # 注意这里要await,让出执行权
        st.session_state.ai_input = ""
        require_update = True
    
    return require_update

async def main():
    """主函数"""
    # 设置页面配置
    st.set_page_config(
        page_title="🎮 LLM Card Studio",
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
        render_action_view()
        
        if await _process_game_loop():
            update_ui_state()

if __name__ == '__main__':

    if "game_manager" not in st.session_state:
       # 初始化游戏状态
       st.session_state.game_manager =  GameManager()
        # 初始化消息列表
       st.session_state.messages = []
    # 初始化卡牌选择状态
    if "card_selection" not in st.session_state:
        st.session_state.card_selection = {
            "is_selecting": False,  # 是否处于选择状态
            "action_type": None,    # 动作类型 (attack/play/etc)
            "target_type": None,    # 目标类型 (opponent_field/opponent_hero)
            "selected_card": None,  # 已选择的卡牌
            "target_card": None,    # 已选择的目标
        }
    asyncio.run(main())

# def main():
#     """主函数"""
#     # 设置页面配置
#     st.set_page_config(
#         page_title="🎮 LLM Card Studio",
#         page_icon="🎮",
#         layout="wide",
#         initial_sidebar_state="collapsed"
#     )
    
#     # 分割界面为游戏区和聊天区
#     game_col, chat_col = st.columns([1, 1])
    
#     # 渲染游戏区
#     with game_col:
#         render_game_view()
    
#     # 渲染聊天区
#     with chat_col:
#         render_chat_view()

# if __name__ == "__main__":
#     main()