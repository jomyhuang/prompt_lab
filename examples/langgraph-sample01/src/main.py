"""主运行文件"""
import asyncio
from game.executor import GameExecutor
from game.models import Card, CardType

async def main():
    """主函数"""
    # 创建测试卡组
    test_deck1 = [
        Card(
            card_id=f"card_{i}",
            name=f"Test Card {i}",
            type=CardType.CREATURE,
            cost={"mana": 1},
            text="Test card text"
        )
        for i in range(40)
    ]
    
    test_deck2 = [
        Card(
            card_id=f"card_{i+40}",
            name=f"Test Card {i+40}",
            type=CardType.CREATURE,
            cost={"mana": 1},
            text="Test card text"
        )
        for i in range(40)
    ]
    
    # 创建执行器
    executor = GameExecutor()
    
    # 创建初始状态
    initial_state = executor.create_initial_state(test_deck1, test_deck2)
    
    try:
        # 执行游戏
        final_state = await executor.execute_game(initial_state)
        print("Game completed!")
        print(f"Final state: {final_state.json(indent=2)}")
    except Exception as e:
        print(f"Game error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
