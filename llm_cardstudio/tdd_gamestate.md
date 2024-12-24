
处理游戏状态循环：
_process_gameloop_state(self):
gameloop_state = self.game_state.get("gameloop_state", "welcome")

状态阶段：
默认为：welcome
    等待玩家按下开始游戏按钮

游戏开始：
start_game：
    _process_game_start()
    初始化游戏数据
    构建deck：（目前先从available_cards中随机生成10张）
deal_cards：
    _process_deal_cards()
    抽取3张牌
determine_first：
    _process_determine_first()
    决定首轮玩家：（目前默认为player）
new_turn：
    _process_new_turn()
    新的回合，回合数+1
player_turn：
    玩家回合，进入player_turn_state子阶段
    _process_player_turn()
        start
        draw_card
        action
        end_turn

opponent_turn：
    对手回合，进入opponent_turn_state子阶段
    _process_opponent_turn()
        start
        draw_card
        action
        end_turn

next_turn：
    _process_next_turn()
    进入下一回合

end_game：
    _process_end_game()
    游戏结束


GUI 渲染：
sidebar
    - 游戏状态信息，默认折叠起来
render_game_view()
    - 负责渲染游戏区
render_chat_view()
    - 负责渲染聊天区与消息
    - 进入player_turn时，渲染玩家操作UI区