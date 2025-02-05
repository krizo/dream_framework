"""
Pokemon Battle Integration Test

This test demonstrates Pokemon battle mechanics using PokeAPI (https://pokeapi.co/).
It showcases a battle between Charizard (Fire/Flying) and Blastoise (Water),
verifying type advantages, stats, and abilities.

API Flow:
1. Base Pokemon data: GET /pokemon/{name}
   - Returns stats, abilities, types
   - Used for initial battle setup
2. Ability details: GET /ability/{id}
   - Returns ability descriptions and effects
   - Used to verify Pokemon capabilities
3. Type relations: GET /type/{id}
   - Returns type effectiveness (2x, 0.5x, 0x damage)
   - Used to calculate battle advantages

Test Flow:
1. Battle Initialization
   - Get both Pokemon base data
   - Load and verify abilities
   - Calculate and store stats
2. Type Analysis
   - Get type relationships
   - Calculate effectiveness multipliers
   - Verify type advantages
3. Battle Verification
   - Confirm correct type matchups
   - Verify stat calculations
   - Validate battle predictions

Example of type advantage:
- Blastoise (Water) vs Charizard (Fire/Flying)
- Water deals 2x damage to Fire
- Therefore Blastoise has type advantage
"""

from typing import Dict, Optional

import pytest
import requests

from core.logger import Log
from core.step import step_start
from core.test_case import TestCase
from helpers.decorators import step


@step(content="Get data from {url}")
def make_request(url: str) -> requests.Response:
    """Make HTTP request and return response."""
    return requests.get(url)


@step(content="Validate response: expected status {status_code}")
def validate_response(response: requests.Response, status_code: int = 200) -> Dict:
    """Validate HTTP response status and return JSON data."""
    assert response.status_code == status_code, \
        f"Expected status {status_code}, got {response.status_code}"
    return response.json()


class PokemonAPI:
    """Helper class for PokeAPI interactions."""

    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2"

    @step(content="Get Pokemon {name} data")
    def get_pokemon(self, name: str) -> Dict:
        """Get Pokemon data by name."""
        response = make_request(f"{self.base_url}/pokemon/{name.lower()}")
        return validate_response(response)

    @step(content="Fetch ability {name}")
    def get_ability(self, name: str, url: str) -> Dict:
        """Get ability details."""
        response = make_request(url)
        data = validate_response(response)
        return data

    @step(content="Getting {type_name} type details")
    def get_type(self, type_name: str) -> Dict:
        """Get type details."""
        response = make_request(f"{self.base_url}/type/{type_name}")
        return validate_response(response)


class PokemonBattleTest(TestCase):
    """
    Test case implementing Pokemon battle mechanics.
    Demonstrates type advantages, stat comparisons, and battle predictions.
    """

    def __init__(self):
        super().__init__(
            name="Pokemon Battle Simulation",
            description="Test Pokemon battle mechanics using PokeAPI",
            test_suite="Pokemon API Tests",
            scope="E2E",
            component="PokeAPI"
        )
        self.api = PokemonAPI()
        self.battle_state: Optional[Dict] = None

    @step(content="Initialize battle: {pokemon1} vs {pokemon2}")
    def initialize_battle(self, pokemon1: str, pokemon2: str) -> None:
        """Set up battle between two Pokemon."""
        self.battle_state = {
            'pokemon1': self._load_pokemon_data(pokemon1),
            'pokemon2': self._load_pokemon_data(pokemon2)
        }

    def _load_pokemon_data(self, name: str) -> Dict:
        """Load complete Pokemon data including abilities and stats."""
        with step_start(f"Getting Pokemon data for {name}"):
            base_data = self.api.get_pokemon(name)

            with step_start("Loading abilities"):
                abilities = []
                for ability_entry in base_data['abilities']:
                    ability_data = self.api.get_ability(
                        ability_entry['ability']['name'],
                        ability_entry['ability']['url']
                    )
                    abilities.append(ability_data)

            with step_start("Processing stats"):
                self._verify_stats(base_data)

            return {
                'name': name,
                'base_data': base_data,
                'abilities': abilities
            }

    @step(content="Calculate type effectiveness")
    def calculate_type_effectiveness(self) -> Dict[str, float]:
        """Calculate type effectiveness for both Pokemon."""
        assert self.battle_state, "Battle must be initialized first"

        effectiveness = {}
        for attacker, defender in [('pokemon1', 'pokemon2'), ('pokemon2', 'pokemon1')]:
            attacker_data = self.battle_state[attacker]
            defender_data = self.battle_state[defender]

            with step_start(f"Analyzing {attacker_data['name']} vs {defender_data['name']}"):
                effectiveness[attacker_data['name']] = self._calculate_multiplier(
                    attacker_data['base_data'],
                    defender_data['base_data']
                )

        return effectiveness

    def _calculate_multiplier(self, attacker: Dict, defender: Dict) -> float:
        """Calculate damage multiplier based on types."""
        multiplier = 1.0
        attacker_types = [t['type']['name'] for t in attacker['types']]
        defender_types = [t['type']['name'] for t in defender['types']]

        for atk_type in attacker_types:
            type_data = self.api.get_type(atk_type)

            for def_type in defender_types:
                if def_type in [t['name'] for t in type_data['damage_relations']['double_damage_to']]:
                    multiplier *= 2
                if def_type in [t['name'] for t in type_data['damage_relations']['half_damage_to']]:
                    multiplier *= 0.5

        return multiplier

    @step(content="Verify Pokemon {pokemon_data[name]} has type {expected_type}")
    def assert_pokemon_has_type(self, pokemon_data: Dict, expected_type: str) -> None:
        """Verify Pokemon has specific type."""
        types = [t['type']['name'] for t in pokemon_data['base_data']['types']]
        assert expected_type in types, \
            f"{pokemon_data['name']} should have {expected_type} type, has {types}"

    @step(content="Verify {pokemon_data[name]} stats")
    def _verify_stats(self, pokemon_data: Dict) -> None:
        """Verify Pokemon has valid stats."""
        for stat in pokemon_data['stats']:
            stat_value = stat['base_stat']
            stat_name = stat['stat']['name']
            assert stat_value > 0, f"{stat_name} should be positive"
            self.add_custom_metric(f"{pokemon_data['name']}_{stat_name}", stat_value)

    @step(content="Verify {pokemon_data[name]} abilities")
    def assert_pokemon_has_abilities(self, pokemon_data: Dict) -> None:
        """Verify Pokemon has abilities."""
        assert pokemon_data['abilities'], f"{pokemon_data['name']} should have abilities"
        for ability in pokemon_data['abilities']:
            assert ability['name'], "Ability should have name"
            self.add_custom_metric(
                f"{pokemon_data['name']}_ability",
                ability['name']
            )

    @step(content="Verify type advantage between {attacker} and {defender}")
    def assert_type_advantage(self, attacker: str, defender: str,
                              effectiveness: Dict[str, float]) -> None:
        """Verify type advantage relationships."""
        assert effectiveness[attacker] != 1.0, \
            f"{attacker} should have type relationship with {defender}"
        assert effectiveness[defender] != 1.0, \
            f"{defender} should have type relationship with {attacker}"

        self.add_custom_metric(f"{attacker}_effectiveness", effectiveness[attacker])
        self.add_custom_metric(f"{defender}_effectiveness", effectiveness[defender])


@pytest.fixture
def pokemon_battle():
    """Fixture providing Pokemon battle test instance."""
    return PokemonBattleTest()


def test_e2e_pokemon_battle_workflow(pokemon_battle):
    """
    Integration test for Pokemon battle mechanics.
    Tests type advantages, stats, and abilities using Charizard vs Blastoise battle.
    """
    Log.info("Starting Pokemon battle test")

    # Initialize battle
    pokemon_battle.initialize_battle("charizard", "blastoise")

    # Verify Pokemon types
    pokemon_battle.assert_pokemon_has_type(
        pokemon_battle.battle_state['pokemon1'],
        "fire"
    )
    pokemon_battle.assert_pokemon_has_type(
        pokemon_battle.battle_state['pokemon2'],
        "water"
    )

    # Verify abilities
    pokemon_battle.assert_pokemon_has_abilities(pokemon_battle.battle_state['pokemon1'])
    pokemon_battle.assert_pokemon_has_abilities(pokemon_battle.battle_state['pokemon2'])

    # Calculate and verify type advantages
    effectiveness = pokemon_battle.calculate_type_effectiveness()
    pokemon_battle.assert_type_advantage("charizard", "blastoise", effectiveness)

    # Water should be super effective against Fire
    assert effectiveness['blastoise'] > effectiveness['charizard'], \
        "Blastoise should have type advantage over Charizard"

    Log.info("Pokemon battle test completed successfully")


def test_e2e_error_handling(pokemon_battle):
    """Test error handling in Pokemon battle scenarios."""
    # Try to calculate effectiveness without initialization
    with pytest.raises(AssertionError) as exc:
        pokemon_battle.calculate_type_effectiveness()
    assert "Battle must be initialized" in str(exc.value)

    # Try to get non-existent Pokemon
    with pytest.raises(Exception):
        pokemon_battle.initialize_battle("nonexistent", "blastoise")
