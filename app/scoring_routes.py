from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Match, Tournament, TournamentType, MatchScore, MatchSchedule, MatchStatus
from app.forms import KyourgiScoreForm, PoomsaeScoreForm, MatchScheduleForm

scoring = Blueprint('scoring', __name__, url_prefix='/scoring')

@scoring.route('/match/<int:match_id>')
@login_required
def match_scoring(match_id):
    match = Match.query.get_or_404(match_id)
    
    if not current_user.can_score_matches():
        flash('You do not have permission to score matches.', 'error')
        return redirect(url_for('main.view_tournament', id=match.tournament_id))
    
    # Get or create scores for both players
    scores = {}
    if match.player1:
        score1 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player1_id).first()
        if not score1:
            score1 = MatchScore(match_id=match_id, player_id=match.player1_id, scored_by=current_user.id)
            db.session.add(score1)
        scores[match.player1_id] = score1
    
    if match.player2:
        score2 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player2_id).first()
        if not score2:
            score2 = MatchScore(match_id=match_id, player_id=match.player2_id, scored_by=current_user.id)
            db.session.add(score2)
        scores[match.player2_id] = score2
    
    db.session.commit()
    
    # Determine form type based on tournament type
    if match.tournament.tournament_type == TournamentType.KYOURGI:
        form = KyourgiScoreForm()
        if match.player1_id in scores:
            form.player1_points.data = scores[match.player1_id].points
            form.player1_warnings.data = scores[match.player1_id].warnings
            form.player1_deductions.data = scores[match.player1_id].deductions
        if match.player2_id in scores:
            form.player2_points.data = scores[match.player2_id].points
            form.player2_warnings.data = scores[match.player2_id].warnings
            form.player2_deductions.data = scores[match.player2_id].deductions
    else:
        form = PoomsaeScoreForm()
        if match.player1_id in scores:
            form.player1_accuracy.data = scores[match.player1_id].accuracy_score
            form.player1_presentation.data = scores[match.player1_id].presentation_score
        if match.player2_id in scores:
            form.player2_accuracy.data = scores[match.player2_id].accuracy_score
            form.player2_presentation.data = scores[match.player2_id].presentation_score
    
    return render_template('scoring/match_scoring.html', 
                         match=match, 
                         form=form, 
                         scores=scores,
                         title=f'Scoring - {match.player1.name if match.player1 else "TBD"} vs {match.player2.name if match.player2 else "TBD"}')

@scoring.route('/match/<int:match_id>/update', methods=['POST'])
@login_required
def update_score(match_id):
    match = Match.query.get_or_404(match_id)
    
    if not current_user.can_score_matches():
        flash('You do not have permission to score matches.', 'error')
        return redirect(url_for('main.view_tournament', id=match.tournament_id))
    
    if match.tournament.tournament_type == TournamentType.KYOURGI:
        form = KyourgiScoreForm()
        if form.validate_on_submit():
            # Update player 1 score
            if match.player1:
                score1 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player1_id).first()
                if not score1:
                    score1 = MatchScore(match_id=match_id, player_id=match.player1_id, scored_by=current_user.id)
                    db.session.add(score1)
                score1.points = form.player1_points.data
                score1.warnings = form.player1_warnings.data
                score1.deductions = form.player1_deductions.data
            
            # Update player 2 score
            if match.player2:
                score2 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player2_id).first()
                if not score2:
                    score2 = MatchScore(match_id=match_id, player_id=match.player2_id, scored_by=current_user.id)
                    db.session.add(score2)
                score2.points = form.player2_points.data
                score2.warnings = form.player2_warnings.data
                score2.deductions = form.player2_deductions.data
            
            # Determine winner based on points
            if match.player1 and match.player2:
                score1 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player1_id).first()
                score2 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player2_id).first()
                
                if score1.points > score2.points:
                    match.winner_id = match.player1_id
                elif score2.points > score1.points:
                    match.winner_id = match.player2_id
                
                match.completed = True
                if match.schedule:
                    match.schedule.status = MatchStatus.COMPLETED
            
    else:  # POOMSAE
        form = PoomsaeScoreForm()
        if form.validate_on_submit():
            # Update player 1 score
            if match.player1:
                score1 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player1_id).first()
                if not score1:
                    score1 = MatchScore(match_id=match_id, player_id=match.player1_id, scored_by=current_user.id)
                    db.session.add(score1)
                score1.accuracy_score = form.player1_accuracy.data
                score1.presentation_score = form.player1_presentation.data
                score1.calculate_total_score()
            
            # Update player 2 score
            if match.player2:
                score2 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player2_id).first()
                if not score2:
                    score2 = MatchScore(match_id=match_id, player_id=match.player2_id, scored_by=current_user.id)
                    db.session.add(score2)
                score2.accuracy_score = form.player2_accuracy.data
                score2.presentation_score = form.player2_presentation.data
                score2.calculate_total_score()
            
            # Determine winner based on total score
            if match.player1 and match.player2:
                score1 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player1_id).first()
                score2 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player2_id).first()
                
                if score1.total_score > score2.total_score:
                    match.winner_id = match.player1_id
                elif score2.total_score > score1.total_score:
                    match.winner_id = match.player2_id
                
                match.completed = True
                if match.schedule:
                    match.schedule.status = MatchStatus.COMPLETED
    
    db.session.commit()
    flash('Scores updated successfully!', 'success')
    return redirect(url_for('scoring.match_scoring', match_id=match_id))

@scoring.route('/live/<int:tournament_id>')
@login_required
def live_scoring(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    if not current_user.can_score_matches():
        flash('You do not have permission to view live scoring.', 'error')
        return redirect(url_for('main.view_tournament', id=tournament_id))
    
    # Get all matches with their scores
    matches = Match.query.filter_by(tournament_id=tournament_id)\
                        .order_by(Match.round_number, Match.match_number).all()
    
    matches_with_scores = []
    for match in matches:
        match_data = {
            'id': match.id,
            'round_number': match.round_number,
            'match_number': match.match_number,
            'category_key': match.category_key,
            'player1': match.player1.name if match.player1 else None,
            'player2': match.player2.name if match.player2 else None,
            'completed': match.completed,
            'winner': match.winner_id
        }
        
        # Get scores
        if match.player1:
            score1 = MatchScore.query.filter_by(match_id=match.id, player_id=match.player1_id).first()
            if score1:
                if tournament.tournament_type == TournamentType.KYOURGI:
                    match_data['player1_score'] = score1.points
                else:
                    match_data['player1_score'] = score1.total_score
        
        if match.player2:
            score2 = MatchScore.query.filter_by(match_id=match.id, player_id=match.player2_id).first()
            if score2:
                if tournament.tournament_type == TournamentType.KYOURGI:
                    match_data['player2_score'] = score2.points
                else:
                    match_data['player2_score'] = score2.total_score
        
        matches_with_scores.append(match_data)
    
    return render_template('scoring/live_scoring.html', 
                         tournament=tournament, 
                         matches=matches_with_scores,
                         title=f'Live Scoring - {tournament.name}')

@scoring.route('/api/match/<int:match_id>/score')
@login_required
def api_match_score(match_id):
    match = Match.query.get_or_404(match_id)
    
    scores = {}
    if match.player1:
        score1 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player1_id).first()
        if score1:
            scores['player1'] = {
                'points': score1.points,
                'warnings': score1.warnings,
                'deductions': score1.deductions,
                'total_score': score1.total_score
            }
    
    if match.player2:
        score2 = MatchScore.query.filter_by(match_id=match_id, player_id=match.player2_id).first()
        if score2:
            scores['player2'] = {
                'points': score2.points,
                'warnings': score2.warnings,
                'deductions': score2.deductions,
                'total_score': score2.total_score
            }
    
    return jsonify({
        'match_id': match_id,
        'completed': match.completed,
        'winner_id': match.winner_id,
        'scores': scores
    })