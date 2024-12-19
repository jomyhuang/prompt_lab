
原本格式:
```json
{
    "card_id": "card_3",
    "instructions": [
      {
        "action": "MOVE_CARD",
        "parameters": {
          "card_id": "card_3",
          "target_position": "field",
          "source": "hand"
        },
        "duration": 0.5,
        "sequence": 1
      },
      {
        "action": "APPLY_EFFECT",
        "parameters": {
          "effect_type": "armor_gain",
          "target_id": "player",
          "value": 5
        },
        "duration": 0.2,
        "sequence": 2
      },
      {
        "action": "SHOW_MESSAGE",
        "parameters": {
          "message": "魔法学徒提升了玩家5点护甲值"
        },
        "duration": 1,
        "sequence": 3
      },
      {
        "action": "PLAY_ANIMATION",
        "parameters": {
          "animation_name": "armor_up",
          "target_id": "player"
        },
        "duration": 0.8,
        "sequence": 4
      }
    ],
    "state_updates": {
      "player_stats.armor": 5
    }
}
```

phase = <phase:drawcard,phase:playcard,phase:attack,phase:defense,phase:endturn> 
1. 将 instructions 序列，改成对应不同阶段的指令序列
2. 指令序列必要一定要有phase:playcard，代表卡牌进场生效，不然其他指令阶段无效
3. phase:drawcard 抽牌时，...
4. phase:attack,phase:defense 进入战斗时，攻击时，防御时，...
5. phase:endturn 回合结束时，...

修改后格式:
```json
{
    "card_id": "card_3",
    "phase:playcard_instructions": [
      {
        "action": "MOVE_CARD",
        "parameters": {
          "card_id": "card_3",
          "target_position": "field",
          "source": "hand"
        },
        "duration": 0.5,
        "sequence": 1
      },
      {
        "action": "APPLY_EFFECT",
        "parameters": {
          "effect_type": "armor_gain",
          "target_id": "player",
          "value": 5
        },
        "duration": 0.2,
        "sequence": 2
      },
      {
        "action": "SHOW_MESSAGE",
        "parameters": {
          "message": "魔法学徒提升了玩家5点护甲值"
        },
        "duration": 1,
        "sequence": 3
      },
      {
        "action": "PLAY_ANIMATION",
        "parameters": {
          "animation_name": "armor_up",
          "target_id": "player"
        },
        "duration": 0.8,
        "sequence": 4
      }
    ],
    "phase:playcard_state_updates": {
      "player_stats.armor": 5
    }
    "<phase:...>_instructions": [
      <list of instructions for the phase>
    ],
    "<phase:...>_state_updates": {
      "player_stats.armor": 5
    }
}
```