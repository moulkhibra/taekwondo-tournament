from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Match, Tournament, MatchSchedule, MatchStatus, User
from app.forms import MatchScheduleForm
from datetime import datetime, timedelta

scheduling = Blueprint('scheduling', __name__, url_prefix='/scheduling')

@scheduling.route('/tournament/<int:tournament_id>')
@login_required
def tournament_schedule(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    if not current_user.can_manage_tournaments():
        flash('You do not have permission to manage schedules.', 'error')
        return redirect(url_for('main.view_tournament', id=tournament_id))
    
    matches = Match.query.filter_by(tournament_id=tournament_id)\
                        .order_by(Match.round_number, Match.match_number).all()
    
    scheduled_matches = []
    unscheduled_matches = []
    
    for match in matches:
        if match.schedule:
            scheduled_matches.append(match)
        else:
            unscheduled_matches.append(match)
    
    return render_template('scheduling/tournament_schedule.html',
                         tournament=tournament,
                         scheduled_matches=scheduled_matches,
                         unscheduled_matches=unscheduled_matches,
                         title=f'Schedule - {tournament.name}')

@scheduling.route('/match/<int:match_id>/schedule', methods=['GET', 'POST'])
@login_required
def schedule_match(match_id):
    match = Match.query.get_or_404(match_id)
    
    if not current_user.can_manage_tournaments():
        flash('You do not have permission to schedule matches.', 'error')
        return redirect(url_for('main.view_tournament', id=match.tournament_id))
    
    form = MatchScheduleForm()
    
    if form.validate_on_submit():
        if match.schedule:
            # Update existing schedule
            match.schedule.scheduled_time = form.scheduled_time.data
            match.schedule.ring_number = form.ring_number.data
            match.schedule.referee_id = form.referee_id.data if form.referee_id.data != 0 else None
            match.schedule.estimated_duration = form.estimated_duration.data
            match.schedule.status = MatchStatus.SCHEDULED
        else:
            # Create new schedule
            schedule = MatchSchedule(
                match_id=match_id,
                scheduled_time=form.scheduled_time.data,
                ring_number=form.ring_number.data,
                referee_id=form.referee_id.data if form.referee_id.data != 0 else None,
                estimated_duration=form.estimated_duration.data,
                status=MatchStatus.SCHEDULED
            )
            db.session.add(schedule)
        
        db.session.commit()
        flash(f'Match scheduled successfully!', 'success')
        return redirect(url_for('scheduling.tournament_schedule', tournament_id=match.tournament_id))
    
    # Pre-fill form if schedule exists
    if match.schedule:
        form.scheduled_time.data = match.schedule.scheduled_time
        form.ring_number.data = match.schedule.ring_number
        form.referee_id.data = match.schedule.referee_id or 0
        form.estimated_duration.data = match.schedule.estimated_duration
    
    return render_template('scheduling/schedule_match.html',
                         match=match,
                         form=form,
                         title=f'Schedule Match - {match.player1.name if match.player1 else "TBD"} vs {match.player2.name if match.player2 else "TBD"}')

@scheduling.route('/match/<int:match_id>/start', methods=['POST'])
@login_required
def start_match(match_id):
    match = Match.query.get_or_404(match_id)
    
    if not current_user.can_score_matches():
        flash('You do not have permission to start matches.', 'error')
        return redirect(url_for('scheduling.tournament_schedule', tournament_id=match.tournament_id))
    
    if match.schedule:
        match.schedule.status = MatchStatus.IN_PROGRESS
        match.schedule.scheduled_time = datetime.utcnow()
        db.session.commit()
        flash('Match started!', 'success')
    else:
        flash('Match must be scheduled first.', 'error')
    
    return redirect(url_for('scoring.match_scoring', match_id=match_id))

@scheduling.route('/match/<int:match_id>/complete', methods=['POST'])
@login_required
def complete_match(match_id):
    match = Match.query.get_or_404(match_id)
    
    if not current_user.can_score_matches():
        flash('You do not have permission to complete matches.', 'error')
        return redirect(url_for('scoring.match_scoring', match_id=match_id))
    
    if match.schedule:
        match.schedule.status = MatchStatus.COMPLETED
        match.completed = True
        db.session.commit()
        flash('Match completed!', 'success')
    
    return redirect(url_for('scheduling.tournament_schedule', tournament_id=match.tournament_id))

@scheduling.route('/api/tournament/<int:tournament_id>/schedule')
@login_required
def api_tournament_schedule(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    schedules = MatchSchedule.query.join(Match)\
                                  .filter(Match.tournament_id == tournament_id)\
                                  .order_by(MatchSchedule.scheduled_time).all()
    
    schedule_data = []
    for schedule in schedules:
        schedule_data.append({
            'id': schedule.id,
            'match_id': schedule.match_id,
            'round_number': schedule.match.round_number,
            'match_number': schedule.match.match_number,
            'category_key': schedule.match.category_key,
            'player1': schedule.match.player1.name if schedule.match.player1 else None,
            'player2': schedule.match.player2.name if schedule.match.player2 else None,
            'scheduled_time': schedule.scheduled_time.isoformat() if schedule.scheduled_time else None,
            'ring_number': schedule.ring_number,
            'referee': schedule.referee.full_name if schedule.referee else None,
            'estimated_duration': schedule.estimated_duration,
            'status': schedule.status.value
        })
    
    return jsonify({
        'tournament_id': tournament_id,
        'tournament_name': tournament.name,
        'schedules': schedule_data
    })

@scheduling.route('/tournament/<int:tournament_id>/auto_schedule', methods=['POST'])
@login_required
def auto_schedule(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    if not current_user.can_manage_tournaments():
        flash('You do not have permission to schedule matches.', 'error')
        return redirect(url_for('scheduling.tournament_schedule', tournament_id=tournament_id))
    
    matches = Match.query.filter_by(tournament_id=tournament_id)\
                        .filter(Match.is_bye == False)\
                        .order_by(Match.round_number, Match.match_number).all()
    
    # Simple auto-scheduling: start from tournament date at 9:00 AM
    start_time = datetime.combine(tournament.date, datetime.min.time().replace(hour=9, minute=0))
    current_time = start_time
    ring_number = 1
    
    for match in matches:
        if not match.schedule:
            # Create schedule
            schedule = MatchSchedule(
                match_id=match.id,
                scheduled_time=current_time,
                ring_number=ring_number,
                estimated_duration=15,
                status=MatchStatus.SCHEDULED
            )
            db.session.add(schedule)
            
            # Move to next time slot
            current_time += timedelta(minutes=15)
            
            # Move to next ring after 8 matches per ring
            if (matches.index(match) + 1) % 8 == 0:
                ring_number += 1
                current_time = start_time  # Reset time for new ring
    
    db.session.commit()
    flash(f'Auto-scheduled {len(matches)} matches!', 'success')
    return redirect(url_for('scheduling.tournament_schedule', tournament_id=tournament_id))