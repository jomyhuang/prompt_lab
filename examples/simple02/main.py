import os
import streamlit as st
from dotenv import load_dotenv
from game_engine.game_manager import GameManager
from game_engine.llm_manager import LLMManager

def main():
    # 加载环境变量
    load_dotenv()
    
    # 初始化LLM管理器
    llm_manager = LLMManager(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    )
    
    # 初始化游戏管理器
    game_manager = GameManager(llm_manager)
    
    # Streamlit界面
    st.title("🎮 对话式卡牌对战游戏")
    
    # 初始化游戏状态
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    
    # 游戏未开始时显示开始界面
    if not st.session_state.game_started:
        st.markdown("欢迎来到对话式卡牌对战游戏！")
        player_name = st.text_input("请输入你的名字：", key="player_name")
        if st.button("开始游戏") and player_name:
            game_state = game_manager.start_game(player_name)
            st.session_state.game_started = True
            st.session_state.game_state = game_state
            st.rerun()
    else:
        # 显示游戏状态
        game_state = st.session_state.game_state
        
        # 显示生命值
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👤 玩家状态")
            st.progress(game_state.current_player.life_points / 4000)
            st.write(f"生命值: {game_state.current_player.life_points}")
            st.write(f"手牌数量: {len(game_state.current_player.hand)}")
        
        with col2:
            st.subheader("🤖 AI对手状态")
            st.progress(game_state.opponent.life_points / 4000)
            st.write(f"生命值: {game_state.opponent.life_points}")
            st.write(f"手牌数量: {len(game_state.opponent.hand)}")
        
        # 显示战场
        st.markdown("---")
        st.subheader("🏰 战场")
        
        # 显示AI场上的卡
        st.write("AI的场地:")
        if game_state.opponent.field:
            for card in game_state.opponent.field:
                st.markdown(f"```\n{card.name}\n攻击: {card.attack} 防御: {card.defense}\n```")
        else:
            st.write("空场地")
        
        # 显示玩家场上的卡
        st.write("你的场地:")
        if game_state.current_player.field:
            for card in game_state.current_player.field:
                st.markdown(f"```\n{card.name}\n攻击: {card.attack} 防御: {card.defense}\n```")
        else:
            st.write("空场地")
        
        # 显示手牌
        st.markdown("---")
        st.subheader("🎴 你的手牌")
        for i, card in enumerate(game_state.current_player.hand):
            st.markdown(f"```\n{i+1}. {card.name}\n类型: {card.type.value}\n攻击: {card.attack} 防御: {card.defense}\n```")
        
        # 用户输入
        st.markdown("---")
        user_input = st.text_input("🎮 输入你的指令:", key="user_input",
                                help="例如：'使用第1张卡'，'攻击对手'，'结束回合'")
        
        if user_input:
            success, message = game_manager.process_user_action(user_input)
            st.write(message)
            
            if success:
                st.rerun()
        
        # 显示游戏日志
        st.markdown("---")
        st.subheader("📜 游戏日志")
        for log in game_state.game_log[-5:]:
            st.write(log)

if __name__ == "__main__":
    main()
