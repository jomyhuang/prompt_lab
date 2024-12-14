import streamlit as st
from game_manager import GameManager
from card_manager import CardManager
from player_manager import PlayerManager
from llm_interaction import LLMInteraction
from card_cost_model import CardCostModel

class StreamlitGUI:
    def __init__(self, game_manager, card_manager, player_manager, llm_interaction, card_cost_model):
        self.game_manager = game_manager
        self.card_manager = card_manager
        self.player_manager = player_manager
        self.llm_interaction = llm_interaction
        self.card_cost_model = card_cost_model
        
        # 初始化游戏状态
        if "initialized" not in st.session_state:
            self.card_manager.draw_cards(5)  # 初始抽5张卡牌
            st.session_state.initialized = True
            st.session_state.game_over = False
            st.session_state.messages = []

    def run(self):
        st.title("🎮 LLM卡牌对战游戏")
        st.markdown("---")

        # 显示游戏状态
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("⚔️ 战斗状态")
            # 使用进度条显示生命值
            st.write("玩家生命值")
            st.progress(self.game_manager.game_state["player_health"] / 100)
            st.write(f"{self.game_manager.game_state['player_health']}/100")
            
            st.write("AI生命值")
            st.progress(self.game_manager.game_state["opponent_health"] / 100)
            st.write(f"{self.game_manager.game_state['opponent_health']}/100")
            
            st.write(f"当前回合: {'玩家' if self.game_manager.game_state['turn'] == 'player' else 'AI'}")

        with col2:
            st.subheader("📜 战斗记录")
            for log in self.game_manager.game_state["log"][-5:]:  # 只显示最近5条记录
                st.write(log)

        # 显示手牌
        st.markdown("---")
        st.subheader("🎴 你的手牌")
        
        # 确保至少有一列
        num_cards = max(1, len(self.card_manager.cards))
        cols = st.columns(num_cards)
        
        # 显示卡牌
        if self.card_manager.cards:
            for idx, (col, card) in enumerate(zip(cols, self.card_manager.cards)):
                with col:
                    st.markdown(f"""
                        ```
                        {card['name']}
                        类型: {card['type']}
                        难度: {self.card_cost_model.calculate_difficulty_score(card)}
                        ```
                    """)
        else:
            st.warning("你的手牌已用完！")

        # 玩家输入
        st.markdown("---")
        user_input = st.text_input("🎮 输入你的指令:", key="user_input")
        
        # 处理玩家输入
        if user_input and not st.session_state.game_over:
            st.session_state.messages.append(("player", user_input))
            
            # 解析玩家动作
            action = self.llm_interaction.parse_user_action(user_input)
            action_result = self.game_manager.process_action(action)
            
            if action_result:
                st.session_state.messages.append(("system", action_result))
            
            # 检查游戏是否结束
            winner = self.game_manager.check_win()
            if winner:
                st.session_state.game_over = True
                st.success(f"游戏结束！{'玩家' if winner == 'player' else 'AI'}获胜！")
                if st.button("重新开始"):
                    st.session_state.clear()
                    st.experimental_rerun()
                return

            # AI回合
            ai_response = self.llm_interaction.generate_ai_response(self.game_manager.game_state)
            if ai_response:
                st.session_state.messages.append(("ai", ai_response))
                ai_action_result = self.game_manager.process_action(ai_response)
                if ai_action_result:
                    st.session_state.messages.append(("system", ai_action_result))

            # 再次检查游戏是否结束
            winner = self.game_manager.check_win()
            if winner:
                st.session_state.game_over = True
                st.success(f"游戏结束！{'玩家' if winner == 'player' else 'AI'}获胜！")
                if st.button("重新开始"):
                    st.session_state.clear()
                    st.experimental_rerun()
                return

            # 显示对话历史
            st.markdown("---")
            st.subheader("💬 对话历史")
            for role, message in st.session_state.messages[-10:]:  # 只显示最近10条消息
                if role == "player":
                    st.write("👤 你：" + message)
                elif role == "ai":
                    st.write("🤖 AI：" + message)
                else:
                    st.write("🎮 系统：" + message)