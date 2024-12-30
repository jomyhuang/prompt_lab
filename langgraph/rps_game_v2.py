import streamlit as st
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
import random

# 定义游戏状态
class GameState(TypedDict):
    player_choice: str
    computer_choice: str
    history: list[str]
    player_wins: int
    computer_wins: int
    game_over: bool

# 初始化游戏状态
def init_game() -> GameState:
    if 'game_state' in st.session_state:
        del st.session_state.game_state
    return GameState(
        player_choice="",
        computer_choice="",
        history=[],
        player_wins=0,
        computer_wins=0,
        game_over=False
    )

def make_move(choice: str):
    st.session_state.game_state["player_choice"] = choice
    st.session_state.game_state = st.session_state.graph.invoke(st.session_state.game_state)
    st.rerun()

# 电脑随机选择
def computer_move(state: GameState) -> GameState:
    if not state["game_over"]:
        choices = ["石头", "剪刀", "布"]
        state["computer_choice"] = random.choice(choices)
    return state

# 判断游戏结果
def judge_game(state: GameState) -> GameState:
    if state["game_over"]:
        return state
        
    player = state["player_choice"]
    computer = state["computer_choice"]
    
    rules = {
        "石头": {"石头": "平局", "剪刀": "你赢了!", "布": "电脑赢了!"},
        "剪刀": {"石头": "电脑赢了!", "剪刀": "平局", "布": "你赢了!"},
        "布": {"石头": "你赢了!", "剪刀": "电脑赢了!", "布": "平局"}
    }
    
    result = rules[player][computer]
    
    # 更新胜场统计
    if "你赢了" in result:
        state["player_wins"] += 1
    elif "电脑赢了" in result:
        state["computer_wins"] += 1
        
    # 检查是否达到胜利条件
    if state["player_wins"] >= 2:
        state["game_over"] = True
        result += " 恭喜你获得最终胜利！"
    elif state["computer_wins"] >= 2:
        state["game_over"] = True
        result += " 电脑获得最终胜利！"
        
    round_num = state["player_wins"] + state["computer_wins"]
    state["history"].append(f"第{round_num}回合：你出了{player}, 电脑出了{computer}. {result}")
    return state

# 构建游戏流程图
def build_graph():
    workflow = StateGraph(GameState)
    
    # 添加节点
    workflow.add_node("computer_move", computer_move)
    workflow.add_node("judge", judge_game)
    
    # 添加边
    workflow.add_edge(START, "computer_move")
    workflow.add_edge("computer_move", "judge")
    workflow.add_edge("judge", END)
    
    return workflow.compile()

# Streamlit界面
def main():
    st.title("剪刀石头布 - 三战二胜制")
    
    # 初始化游戏状态
    if "game_state" not in st.session_state:
        st.session_state.game_state = init_game()
        st.session_state.graph = build_graph()
    
    # 显示当前比分
    st.subheader("当前比分")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("玩家得分", st.session_state.game_state["player_wins"])
    with col2:
        st.metric("电脑得分", st.session_state.game_state["computer_wins"])
    
    # 如果游戏未结束，显示选择按钮
    if not st.session_state.game_state["game_over"]:
        st.subheader("请选择你的出招")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("石头", key="rock"):
                make_move("石头")
        with col2:
            if st.button("剪刀", key="scissors"):
                make_move("剪刀")
        with col3:
            if st.button("布", key="paper"):
                make_move("布")
    else:
        st.info("游戏已结束！")
    
    # 显示游戏历史
    st.subheader("对战记录")
    for record in st.session_state.game_state["history"]:
        st.write(record)
    
    # 重置游戏按钮
    if st.button("重新开始新的比赛", key="restart"):
        st.session_state.game_state = init_game()
        st.rerun()

if __name__ == "__main__":
    main()
