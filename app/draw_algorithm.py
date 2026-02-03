from app.models import Player, Tournament, TournamentType, Gender, AgeGroup, WeightCategory
import random

class TournamentDrawAlgorithm:
    """
    Qor3a (قرعة) - Arabic for "draw" or "lottery"
    Tournament draw algorithm for Taekwondo competitions
    """
    
    def __init__(self, tournament):
        self.tournament = tournament
        self.players = []  # Will be set externally
        self.players_by_category = self._categorize_players()
    
    def _categorize_players(self):
        """
        Group players by category based on tournament type
        Returns dictionary with category keys and player lists
        """
        categorized = {}
        
        # This will be called after players are set
        if hasattr(self, 'players'):
            for player in self.players:
                category_key = self._get_category_key(player)
                if category_key not in categorized:
                    categorized[category_key] = []
                categorized[category_key].append(player)
        
        return categorized
    
    def _get_category_key(self, player):
        """Generate category key for grouping players"""
        if self.tournament.tournament_type == TournamentType.KYOURGI:
            return f"{player.gender.value}_{player.age_group.value}_{player.weight_category.value}"
        else:  # POOMSAE
            return f"{player.gender.value}_{player.age_group.value}"
    
    def _determine_age_group(self, age):
        """Determine age group based on player age"""
        if age <= 17:
            return AgeGroup.CADET
        elif age <= 34:
            return AgeGroup.JUNIOR
        else:
            return AgeGroup.SENIOR
    
    def _determine_weight_category(self, weight):
        """Determine weight category based on player weight"""
        if weight <= 68:
            return WeightCategory.LIGHT
        elif weight <= 80:
            return WeightCategory.MIDDLE
        else:
            return WeightCategory.HEAVY
    
    def _shuffle_players(self, players):
        """Randomly shuffle players for fair draw"""
        shuffled = players.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def _create_first_round_matches(self, category_players, category_key):
        """
        Create first round matches for a category
        Handles odd number of players with BYE
        """
        shuffled_players = self._shuffle_players(category_players)
        matches = []
        player_count = len(shuffled_players)
        
        # Handle odd number of players - give BYE to random player
        bye_player = None
        if player_count % 2 == 1:
            # Randomly select a player for BYE
            bye_player = random.choice(shuffled_players)
            shuffled_players.remove(bye_player)
            
            # Create BYE match
            bye_match = {
                'round': 1,
                'match_number': 1,
                'player1': bye_player,
                'player2': None,
                'category_key': category_key,
                'is_bye': True
            }
            matches.append(bye_match)
        
        # Create regular matches
        match_number = 2 if bye_player else 1
        for i in range(0, len(shuffled_players), 2):
            if i + 1 < len(shuffled_players):
                match = {
                    'round': 1,
                    'match_number': match_number,
                    'player1': shuffled_players[i],
                    'player2': shuffled_players[i + 1],
                    'category_key': category_key,
                    'is_bye': False
                }
                matches.append(match)
                match_number += 1
            else:
                # This shouldn't happen with proper BYE handling
                solo_match = {
                    'round': 1,
                    'match_number': match_number,
                    'player1': shuffled_players[i],
                    'player2': None,
                    'category_key': category_key,
                    'is_bye': True
                }
                matches.append(solo_match)
        
        return matches
    
    def generate_draw(self):
        """
        Generate complete tournament draw
        Returns dictionary with categories and their matches
        """
        tournament_draw = {}
        
        for category_key, category_players in self.players_by_category.items():
            if not category_players:
                continue
                
            # Generate first round matches
            first_round_matches = self._create_first_round_matches(category_players, category_key)
            
            # Calculate total rounds needed (power of 2)
            player_count = len(category_players)
            next_power_of_2 = 1
            while next_power_of_2 < player_count:
                next_power_of_2 *= 2
            total_rounds = next_power_of_2.bit_length() - 1
            
            # Generate subsequent rounds (placeholder structure)
            all_matches = first_round_matches
            for round_num in range(2, total_rounds + 1):
                # These matches will be filled as tournament progresses
                # For now, create empty placeholders
                expected_matches = len(first_round_matches) // (2 ** (round_num - 1))
                for match_num in range(1, expected_matches + 1):
                    placeholder = {
                        'round': round_num,
                        'match_number': match_num,
                        'player1': None,
                        'player2': None,
                        'category_key': category_key,
                        'is_bye': False,
                        'is_placeholder': True
                    }
                    all_matches.append(placeholder)
            
            tournament_draw[category_key] = {
                'category_name': self._get_category_name(category_key),
                'players': category_players,
                'matches': all_matches,
                'total_rounds': total_rounds
            }
        
        return tournament_draw
    
    def _get_category_name(self, category_key):
        """Convert category key to human-readable name"""
        parts = category_key.split('_')
        gender = 'Male' if parts[0] == 'male' else 'Female'
        age_group = parts[1].title()
        
        if self.tournament.tournament_type == TournamentType.KYOURGI:
            weight = parts[2].title()
            return f"{gender} {age_group} {weight} Kyourgi"
        else:
            return f"{gender} {age_group} Poomsae"
    
    def save_to_database(self, tournament_draw):
        """Save generated draw to database"""
        from app import db
        from app.models import Match, Player
        
        # Clear existing matches for this tournament
        Match.query.filter_by(tournament_id=self.tournament.id).delete()
        db.session.commit()
        
        # Save new matches
        for category_key, category_data in tournament_draw.items():
            for match_data in category_data['matches']:
                # Only save actual matches, not placeholders
                if not match_data.get('is_placeholder', False):
                    match = Match()
                    match.round_number = match_data['round']
                    match.match_number = match_data['match_number']
                    match.player1_id = match_data['player1'].id if match_data['player1'] else None
                    match.player2_id = match_data['player2'].id if match_data['player2'] else None
                    match.is_bye = match_data['is_bye']
                    match.tournament_id = self.tournament.id
                    match.category_key = category_key
                    db.session.add(match)
        
        db.session.commit()