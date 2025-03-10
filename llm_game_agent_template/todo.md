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


##thinking topic:
GUI-LangGraph Agent的框架关系处理
UI - state messages 相互的关系

AutoUI处理 - 
自动处理Agent结束后,需要自动更新的UI, 然后再进入HIL

turn switch 处理 -
由 _player_turn 跟 _ai_turn 自己处理


LLM_interaction 不同模版注入
或是定义给搭配给agent tool使用?
Runnalable configurate study 


处理messages 的流动
所有的message都要上GUI的chat_view 或两个flow?
- 提示信息
- 游戏交互反馈
- 来自chat类agent的反馈


都往main pool更新,不需要经过game agent
保持独立性
跟对话性(两个agent直接的对话)


合成对话指令
更精确(通过chat-tool)的执行
或是/ 跳过chat执行,直接执行tool(或代码)


def agent(state) -> Command[Literal["agent", "another_agent"]]:
def agent(state) -> Literal["agent", "another_agent"]:


思考需要mock session 同步问题,如果可以直接取值
graph.get_state(thread).values (取值?)


chat+tool 放在node在哪里(理论上在route)?
在player node 跳转后返回

main agent如何挂入assiant (chat)
更新gameboard是?
“游戏”主体是?



## todo:









## issue:


[ ]- 测试 Tool node
[ ]- 测试 chat message 不同的组件
    - 回复格式 parser

[ ]- 切换不同game+game_agent
    - GUI 层只提供合成指令UI, state 渲染
[ ]- 假设有个扑克牌在里面, 
    - 跟AI 想玩任何?
    - 载入不同prompt 连接上下文

[ ]- 将chat包在agent内
[ ]- 持久化 save/load



##bug fix:

[x]- 测试messages: Annotated[list, add_messages]
在stream模式下, 更新message异常.
1. 每个node的输出, 都确保只更新该node的输出, 不要更新全部的state.
2. 同步更新GUI state的方式(支持Annotated[list, add_messages])

1/18 0.2.60
streaming 下(测试invoke模式是正确的)
Annotated[list, add_messages]
异常 

1. init + welcome 可以正常
2. route 异常,变成全部overwrite
3. player_turn, 变成全部overwrite
4. 如果有个node没有message, 则会出现所有信息(异常)

[x]- BUG FIX: json.dump 无法处理 messages Annotated下, HumanMessage..特别格式
不需要处理直接注入, 但要注意是tuples类型
```
game_state: {'game_started': True, 'messages': [HumanMessage(content='_route_state 2025-01-05T23:37:46.883974', additional_kwargs={}, response_metadata={}, id='ba31f06f-7764-4d45-8bbf-1ed0c468aa28'), HumanMessage(content='_player_turn 2025-01-05T23:38:21.690249', additional_kwargs={}, response_metadata={}, id='8646d7bd-f0b6-4997-bf40-26afc78906e2'), HumanMessage(content='_route_state 2025-01-05T23:38:21.695253', additional_kwargs={}, response_metadata={}, id='76f301b3-6721-4699-b1db-a9d2b4868330')], 'current_turn': 'end_game', 'game_over': True, 'game_data': {}, 'last_action': 'game_over', 'phase': 'game over', 'valid_actions': ['play', 'end_turn', 'game_over'], 'thread_id': 'bfc72758-2ecc-4455-affe-f2ba7f05d14d', 'info': '游戏结束'}
```


## reference links:

https://alejandro-ao.com/how-to-use-streaming-in-langchain-and-streamlit/

https://github.com/shiv248/Streamlit-x-LangGraph-Cookbooks

how-to-guide 中文
https://github.com/jurnea/LangGraph-Chinese/blob/master/HowtoGuides.md



## tips, codeblocks
1. add_messages 支持 []
state["messages"]= [AIMessage(content=f"_welcome_state {datetime.now()}")]
or/ 都可以
AIMessage(content=f"_init_state {datetime.now()}")



## 参考最新API文件：
streamlit API
https://docs.streamlit.io
https://docs.streamlit.io/develop/api-reference

langchain api
https://python.langchain.com/api_reference/

pydantic
https://docs.pydantic.dev/latest/


## notepad:
Always respond in 中文，请正确使用UTF-8中文编码
并且不要对已经存在的变量,注释,常量等的中文编码错误进行修改
不要任意将已经注释或是代码注释尝试删除
专注处理所下达指令的修改, 不要任意修改指令以外其他的动作, 比如任意删除注释,代码或是尝试同时重构代码

技术栈:
1. python
2. langchain > 0.3.11
3. pydantic > 2.10.3
4. streamlit > 1.14.0