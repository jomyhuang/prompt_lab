import streamlit as st
from streamlit.components.v1 import html

def render_card(card: str) -> str:
    """渲染单张扑克牌的HTML"""
    rank = card[:-1]
    suit = card[-1]
    
    # 花色的颜色和符号映射
    suit_map = {
        "♠": ("black", "♠"),
        "♥": ("red", "♥"),
        "♦": ("red", "♦"),
        "♣": ("black", "♣")
    }
    color, symbol = suit_map[suit]
    
    return f"""
    <div style="
        display: inline-block;
        width: 60px;
        height: 90px;
        margin: 5px;
        padding: 5px;
        border: 2px solid #ccc;
        border-radius: 8px;
        background: white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        text-align: center;
        font-family: Arial;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: 5px;
            left: 5px;
            color: {color};
            font-size: 16px;
        ">{rank}</div>
        <div style="
            position: absolute;
            bottom: 5px;
            right: 5px;
            color: {color};
            font-size: 16px;
        ">{rank}</div>
        <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: {color};
            font-size: 24px;
        ">{symbol}</div>
    </div>
    """

def render_cards(cards: list[str], hidden: bool = False) -> None:
    """渲染一组扑克牌
    Args:
        cards: 要显示的卡牌列表
        hidden: 是否隐藏除第一张外的其他牌
    """
    html_cards = []
    for i, card in enumerate(cards):
        if hidden and i > 0:
            # 渲染背面 - 使用菱形网格图案
            html_cards.append(f"""
            <div style="
                display: inline-block;
                width: 60px;
                height: 90px;
                margin: 5px;
                padding: 5px;
                border: 2px solid #666;
                border-radius: 8px;
                background: linear-gradient(135deg, 
                    #8b0000 25%, 
                    #b22222 25%, 
                    #b22222 50%, 
                    #8b0000 50%, 
                    #8b0000 75%, 
                    #b22222 75%
                );
                background-size: 15px 15px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                position: relative;
            ">
                <div style="
                    position: absolute;
                    top: 5px;
                    left: 5px;
                    right: 5px;
                    bottom: 5px;
                    border: 2px solid rgba(255,255,255,0.2);
                    border-radius: 4px;
                "></div>
            </div>
            """)
        else:
            html_cards.append(render_card(card))
    
    # 组合所有卡牌的HTML
    cards_html = "\n".join(html_cards)
    container_html = f"""
    <div style="
        padding: 10px;
        border-radius: 10px;
        background: #f0f0f0;
        display: inline-block;
    ">
        {cards_html}
    </div>
    """
    
    # 使用streamlit的html组件显示
    html(container_html, height=130) 