
5. 指令序列嵌套到发动的阶段：'drawcard_phase','playcard_phase','attack_phase','end_phase'


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

修改后格式:
```json
{
    "card_id": "card_3",
    "playcard_instructions": [
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
    "<phase:>_instructions": [
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