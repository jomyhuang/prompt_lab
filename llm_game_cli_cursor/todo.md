# todo.md


## 01/03/2025
-[x] 输入对话后, user_chat_input 无法直接刷新
streaming test
https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps

## 01/05/2025
[x]- 测试 langgraph streaming
[x]- interrupt -> resume 后, 如何正确只有一次进入该node信息
    - stream 模式下, 可以取得所有node信息, 但是需要处理 (包含interrupt)
    - 在run_agent_stream下处理 chunk处理+同步处理
        - set_game_state -> st.session_state.game_agent.game_state
        - set_game_interrupt -> st.session_state.game_agent.interrupt_state
[x]- 暂时取消async模式呼叫, streaming模式 + loop flag处理
    - 输入"对话/指令"时候, 先render st.session_state.messages的变更flag, 让后在进行下一步
    - require_update_chat flag
    - require_update


##topic:
GUI-LangGraph Agent的框架关系处理
messages 的更新
在AI turn过程中,如果更新message,跟HIL

route处理turn switch, 还是需要一个end_turn node
tool 放在node在哪里(理论上在route)?




## todo:

测试messages: Annotated[list, add_messages]
BUG issue:





[ ]- 测试 Tool node
[ ]- 测试 chat message 不同的组件
    - 回复格式 parser

[ ]- 切换不同game_agent
    - GUI 层只提供合成指令UI, state 渲染
[ ]- 假设有个扑克牌在里面, 
    - 跟AI 想玩任何?
    - 载入不同prompt 连接上下文

[ ]- 将chat包在agent内
[ ]- 持久化 save/load

##bug fix:
[ ]- BUG FIX: json.dump 无法处理 messages Annotated下, HumanMessage..特别格式 
```
game_state: {'game_started': True, 'messages': [HumanMessage(content='_route_state 2025-01-05T23:37:46.883974', additional_kwargs={}, response_metadata={}, id='ba31f06f-7764-4d45-8bbf-1ed0c468aa28'), HumanMessage(content='_player_turn 2025-01-05T23:38:21.690249', additional_kwargs={}, response_metadata={}, id='8646d7bd-f0b6-4997-bf40-26afc78906e2'), HumanMessage(content='_route_state 2025-01-05T23:38:21.695253', additional_kwargs={}, response_metadata={}, id='76f301b3-6721-4699-b1db-a9d2b4868330')], 'current_turn': 'end_game', 'game_over': True, 'game_data': {}, 'last_action': 'game_over', 'phase': 'game over', 'valid_actions': ['play', 'end_turn', 'game_over'], 'thread_id': 'bfc72758-2ecc-4455-affe-f2ba7f05d14d', 'info': '游戏结束'}
```




## reference links:

https://alejandro-ao.com/how-to-use-streaming-in-langchain-and-streamlit/

https://github.com/shiv248/Streamlit-x-LangGraph-Cookbooks

how-to-guide 中文
https://github.com/jurnea/LangGraph-Chinese/blob/master/HowtoGuides.md
