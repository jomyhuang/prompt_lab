from game_manager import GameManager
from card_manager import CardManager
from player_manager import PlayerManager
from llm_interaction import LLMInteraction
from streamlit_gui import StreamlitGUI
from card_cost_model import CardCostModel

if __name__ == "__main__":
    game_manager = GameManager()
    card_manager = CardManager()
    player_manager = PlayerManager()
    llm_interaction = LLMInteraction()
    card_cost_model = CardCostModel()
    gui = StreamlitGUI(game_manager,card_manager, player_manager, llm_interaction, card_cost_model)
    gui.run()
