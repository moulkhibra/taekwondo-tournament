from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Tournament, Player, Match, MatchScore, JudgeScore, TournamentType, Gender, AgeGroup, WeightCategory, User
from app.forms import TournamentForm, PlayerForm, CategoryFilterForm, DrawForm
from app.draw_algorithm import TournamentDrawAlgorithm
from app.excel_utils import ExcelImportExport, ExcelImportError
import io
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Main dashboard page"""
    tournaments = Tournament.query.order_by(Tournament.date.desc()).all()
    return render_template('dashboard.html', tournaments=tournaments)

@main.route('/tournament/new', methods=['GET', 'POST'])
def create_tournament():
    """Create new tournament"""
    form = TournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(
            name=form.name.data,
            date=form.date.data,
            location=form.location.data,
            tournament_type=TournamentType(form.tournament_type.data)
        )
        db.session.add(tournament)
        db.session.commit()
        flash(f'Tournament "{tournament.name}" created successfully!', 'success')
        return redirect(url_for('main.view_tournament', id=tournament.id))
    
    return render_template('tournament_form.html', form=form, title='Create Tournament')

@main.route('/tournament/<int:id>')
def view_tournament(id):
    """View tournament details"""
    tournament = Tournament.query.get_or_404(id)
    filter_form = CategoryFilterForm()
    players = Player.query.filter_by(tournament_id=id).all()
    matches = Match.query.filter_by(tournament_id=id).order_by(Match.round_number, Match.match_number).all()
    
    # Apply filters if submitted
    if request.args.get('gender') or request.args.get('age_group') or request.args.get('weight_category'):
        filtered_players = []
        for player in players:
            include = True
            if request.args.get('gender') and player.gender.value != request.args.get('gender'):
                include = False
            if request.args.get('age_group') and player.age_group.value != request.args.get('age_group'):
                include = False
            if request.args.get('weight_category') and player.weight_category and player.weight_category.value != request.args.get('weight_category'):
                include = False
            if include:
                filtered_players.append(player)
        players = filtered_players
    
    # Group matches by category for display
    matches_by_category = {}
    for match in matches:
        if match.category_key not in matches_by_category:
            matches_by_category[match.category_key] = []
        matches_by_category[match.category_key].append(match)
    
    return render_template('tournament_view.html', 
                         tournament=tournament, 
                         players=players, 
                         matches_by_category=matches_by_category,
                         filter_form=filter_form)

@main.route('/player/new', methods=['GET', 'POST'])
def create_player():
    """Add new player"""
    form = PlayerForm()
    if form.validate_on_submit():
        # Get tournament to determine type
        tournament = Tournament.query.get(form.tournament_id.data)
        
        # Determine age group
        if form.age.data <= 17:
            age_group = AgeGroup.CADET
        elif form.age.data <= 34:
            age_group = AgeGroup.JUNIOR
        else:
            age_group = AgeGroup.SENIOR
        
        # Determine weight category for Kyourgi
        weight_category = None
        if tournament.tournament_type == TournamentType.KYOURGI and form.weight.data:
            if form.weight.data <= 68:
                weight_category = WeightCategory.LIGHT
            elif form.weight.data <= 80:
                weight_category = WeightCategory.MIDDLE
            else:
                weight_category = WeightCategory.HEAVY
        
        player = Player(
            name=form.name.data,
            club=form.club.data,
            gender=Gender(form.gender.data),
            age=form.age.data,
            weight=form.weight.data,
            age_group=age_group,
            weight_category=weight_category,
            tournament_id=form.tournament_id.data
        )
        
        db.session.add(player)
        db.session.commit()
        flash(f'Player "{player.name}" added successfully!', 'success')
        return redirect(url_for('main.view_tournament', id=form.tournament_id.data))
    
    return render_template('player_form.html', form=form, title='Add Player')

@main.route('/player/<int:id>/edit', methods=['GET', 'POST'])
def edit_player(id):
    """Edit existing player"""
    player = Player.query.get_or_404(id)
    form = PlayerForm(obj=player)
    
    if form.validate_on_submit():
        # Update fields
        player.name = form.name.data
        player.club = form.club.data
        player.gender = Gender(form.gender.data)
        player.age = form.age.data
        player.weight = form.weight.data
        
        # Recalculate age group
        if form.age.data <= 17:
            player.age_group = AgeGroup.CADET
        elif form.age.data <= 34:
            player.age_group = AgeGroup.JUNIOR
        else:
            player.age_group = AgeGroup.SENIOR
        
        # Recalculate weight category for Kyourgi
        if player.tournament.tournament_type == TournamentType.KYOURGI and form.weight.data:
            if form.weight.data <= 68:
                player.weight_category = WeightCategory.LIGHT
            elif form.weight.data <= 80:
                player.weight_category = WeightCategory.MIDDLE
            else:
                player.weight_category = WeightCategory.HEAVY
        else:
            player.weight_category = None
        
        db.session.commit()
        flash(f'Player "{player.name}" updated successfully!', 'success')
        return redirect(url_for('main.view_tournament', id=player.tournament_id))
    
    return render_template('player_form.html', form=form, title='Edit Player', player=player)

@main.route('/player/<int:id>/delete', methods=['POST'])
def delete_player(id):
    """Delete player"""
    player = Player.query.get_or_404(id)
    tournament_id = player.tournament_id
    name = player.name
    
    db.session.delete(player)
    db.session.commit()
    flash(f'Player "{name}" deleted successfully!', 'success')
    return redirect(url_for('main.view_tournament', id=tournament_id))

@main.route('/draw/generate', methods=['GET', 'POST'])
def generate_draw():
    """Generate tournament draw"""
    form = DrawForm()
    
    if form.validate_on_submit():
        tournament = Tournament.query.get(form.tournament_id.data)
        players = Player.query.filter_by(tournament_id=form.tournament_id.data).all()
        
        if not players:
            flash('No players found for this tournament!', 'error')
            return redirect(url_for('main.generate_draw'))
        
        # Generate draw using algorithm
        draw_algorithm = TournamentDrawAlgorithm(tournament)
        draw_algorithm.players = players  # Set the players
        tournament_draw = draw_algorithm.generate_draw()
        
        # Save to database
        draw_algorithm.save_to_database(tournament_draw)
        
        flash(f'Tournament draw generated for "{tournament.name}"!', 'success')
        return redirect(url_for('main.view_tournament', id=tournament.id))
    
    return render_template('draw_form.html', form=form, title='Generate Draw')

@main.route('/export/tournament/<int:id>/<format>')
def export_tournament(id, format):
    """Export tournament data"""
    tournament = Tournament.query.get_or_404(id)
    players = Player.query.filter_by(tournament_id=id).all()
    matches = Match.query.filter_by(tournament_id=id).order_by(Match.round_number, Match.match_number).all()
    
    if format == 'text':
        return export_as_text(tournament, players, matches)
    elif format == 'pdf':
        return export_as_pdf(tournament, players, matches)
    else:
        flash('Invalid export format!', 'error')
        return redirect(url_for('main.view_tournament', id=id))

def export_as_text(tournament, players, matches):
    """Export tournament as plain text"""
    output = io.StringIO()
    
    # Tournament info
    output.write(f"TOURNAMENT: {tournament.name}\n")
    output.write(f"Date: {tournament.date}\n")
    output.write(f"Location: {tournament.location}\n")
    output.write(f"Type: {tournament.tournament_type.value.title()}\n")
    output.write("=" * 50 + "\n\n")
    
    # Players list
    output.write("REGISTERED PLAYERS:\n")
    output.write("-" * 30 + "\n")
    for i, player in enumerate(players, 1):
        weight_info = f" ({player.weight}kg)" if player.weight else ""
        output.write(f"{i:2d}. {player.name} - {player.club} - {player.gender.value} {player.age}y{weight_info}\n")
    
    output.write("\n")
    
    # Matches by category
    matches_by_category = {}
    for match in matches:
        if match.category_key not in matches_by_category:
            matches_by_category[match.category_key] = []
        matches_by_category[match.category_key].append(match)
    
    output.write("TOURNAMENT DRAW:\n")
    output.write("-" * 30 + "\n")
    
    for category_key, category_matches in matches_by_category.items():
        # Convert category key to readable name
        parts = category_key.split('_')
        gender = 'Male' if parts[0] == 'male' else 'Female'
        age_group = parts[1].title()
        if tournament.tournament_type == TournamentType.KYOURGI:
            weight = parts[2].title()
            category_name = f"{gender} {age_group} {weight} Kyourgi"
        else:
            category_name = f"{gender} {age_group} Poomsae"
        
        output.write(f"\n{category_name}:\n")
        
        # Group by rounds
        rounds = {}
        for match in category_matches:
            if match.round_number not in rounds:
                rounds[match.round_number] = []
            rounds[match.round_number].append(match)
        
        for round_num in sorted(rounds.keys()):
            output.write(f"  Round {round_num}:\n")
            for match in rounds[round_num]:
                if match.is_bye:
                    player_name = match.player1.name if match.player1 else "Unknown"
                    output.write(f"    BYE: {player_name}\n")
                else:
                    p1_name = match.player1.name if match.player1 else "TBD"
                    p2_name = match.player2.name if match.player2 else "TBD"
                    output.write(f"    {p1_name} vs {p2_name}\n")
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename={tournament.name.replace(" ", "_")}_draw.txt'
    return response

def export_as_pdf(tournament, players, matches):
    """Export tournament as PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"<b>{tournament.name}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Tournament info
    info_text = f"""
    Date: {tournament.date}<br/>
    Location: {tournament.location}<br/>
    Type: {tournament.tournament_type.value.title()}<br/>
    Total Players: {len(players)}
    """
    info = Paragraph(info_text, styles['Normal'])
    story.append(info)
    story.append(Spacer(1, 20))
    
    # Players table
    story.append(Paragraph("<b>Registered Players</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    player_data = [['#', 'Name', 'Club', 'Gender', 'Age', 'Weight']]
    for i, player in enumerate(players, 1):
        weight = f"{player.weight}kg" if player.weight else "N/A"
        player_data.append([str(i), player.name, player.club, player.gender.value, str(player.age), weight])
    
    player_table = Table(player_data)
    player_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(player_table)
    story.append(Spacer(1, 20))
    
    # Draw information
    story.append(Paragraph("<b>Tournament Draw</b>", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    # Group matches by category
    matches_by_category = {}
    for match in matches:
        if match.category_key not in matches_by_category:
            matches_by_category[match.category_key] = []
        matches_by_category[match.category_key].append(match)
    
    for category_key, category_matches in matches_by_category.items():
        # Category name
        parts = category_key.split('_')
        gender = 'Male' if parts[0] == 'male' else 'Female'
        age_group = parts[1].title()
        if tournament.tournament_type == TournamentType.KYOURGI:
            weight = parts[2].title()
            category_name = f"{gender} {age_group} {weight} Kyourgi"
        else:
            category_name = f"{gender} {age_group} Poomsae"
        
        story.append(Paragraph(f"<b>{category_name}</b>", styles['Heading3']))
        
        # Match data
        match_data = [['Round', 'Match', 'Player 1', 'Player 2', 'Status']]
        for match in sorted(category_matches, key=lambda x: (x.round_number, x.match_number)):
            if match.is_bye:
                player1_name = match.player1.name if match.player1 else "Unknown"
                match_data.append([str(match.round_number), str(match.match_number), f"BYE: {player1_name}", "", "BYE"])
            else:
                p1_name = match.player1.name if match.player1 else "TBD"
                p2_name = match.player2.name if match.player2 else "TBD"
                status = "Completed" if match.completed else "Pending"
                match_data.append([str(match.round_number), str(match.match_number), p1_name, p2_name, status])
        
        match_table = Table(match_data)
        match_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7)
        ]))
        story.append(match_table)
        story.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Create response
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={tournament.name.replace(" ", "_")}_draw.pdf'
    return response

# Excel Integration Routes

@main.route('/excel/import_players/<int:tournament_id>', methods=['GET', 'POST'])
def excel_import_players(tournament_id):
    """Import players from Excel file"""
    tournament = Tournament.query.get_or_404(tournament_id)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        try:
            success_count, error_list = ExcelImportExport.import_players_from_excel(file, tournament_id)
            
            # Flash success message
            flash(f'Successfully imported {success_count} players!', 'success')
            
            # Flash errors (if any)
            if error_list:
                flash(f'{len(error_list)} rows had errors and were skipped:', 'warning')
                for error in error_list[:5]:  # Show first 5 errors
                    flash(error, 'warning')
                if len(error_list) > 5:
                    flash(f'... and {len(error_list) - 5} more errors', 'warning')
            
            return redirect(url_for('main.view_tournament', id=tournament_id))
            
        except ExcelImportError as e:
            flash(f'Error importing file: {str(e)}', 'error')
            return redirect(request.url)
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('excel_import.html', tournament=tournament, title='Import Players from Excel')

@main.route('/excel/export_brackets/<int:tournament_id>')
def excel_export_brackets(tournament_id):
    """Export tournament brackets to Excel"""
    try:
        excel_file = ExcelImportExport.export_brackets_to_excel(tournament_id)
        tournament = Tournament.query.get(tournament_id)
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f'{tournament.name.replace(" ", "_")}_brackets.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except ExcelImportError as e:
        flash(f'Error exporting brackets: {str(e)}', 'error')
        return redirect(url_for('main.view_tournament', id=tournament_id))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return redirect(url_for('main.view_tournament', id=tournament_id))

@main.route('/excel/download_template')
def excel_download_template():
    """Download Excel template for player import"""
    try:
        template_file = ExcelImportExport.create_import_template()
        
        return send_file(
            template_file,
            as_attachment=True,
            download_name='player_import_template.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        flash(f'Error generating template: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@main.route('/import/googleforms/<int:tournament_id>', methods=['GET', 'POST'])
def import_google_forms(tournament_id):
    """Import players from Google Forms Excel file"""
    tournament = Tournament.query.get_or_404(tournament_id)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        try:
            # Read Excel file
            file.seek(0)
            df = pd.read_excel(file, engine='openpyxl')
            
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            
            # Check required columns (Arabic headers)
            required_columns = [
                'الجمعية و المدينة (بالعربية)',
                'اسم المدرب أو الرئيس', 
                'الاسم الكامل في حالة الفردي( أو اسمين أو ثلاثة في حالة الزوجي و الفريق)',
                'الصنف',
                'اختر الفئة المناسبة'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                return redirect(request.url)
            
            success_count = 0
            error_list = []
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Extract data from Arabic columns
                    club = str(row['الجمعية و المدينة (بالعربية)']).strip()
                    coach = str(row['اسم المدرب أو الرئيس']).strip()
                    name = str(row['الاسم الكامل في حالة الفردي( أو اسمين أو ثلاثة في حالة الزوجي و الفريق)']).strip()
                    gender_raw = str(row['الصنف']).strip()
                    age_group_raw = str(row['اختر الفئة المناسبة']).strip()
                    
                    # Skip empty rows
                    if not name or name.lower() == 'nan':
                        continue
                    if not club or club.lower() == 'nan':
                        continue
                    
                    # Map gender
                    gender_mapping = {
                        'ذكر': 'male',
                        'إناث': 'female', 
                        'بنين': 'male',
                        'بنات': 'female',
                        'male': 'male',
                        'female': 'female',
                        'M': 'male',
                        'F': 'female'
                    }
                    gender = gender_mapping.get(gender_raw.lower(), None)
                    if not gender:
                        error_list.append(f"Row {index + 2}: Invalid gender '{gender_raw}'")
                        continue
                    
                    # Map age group
                    age_group_mapping = {
                        'الناشئين': 'cadet',
                        'شباب': 'junior',
                        'كبار': 'senior',
                        'cadet': 'cadet',
                        'junior': 'junior', 
                        'senior': 'senior',
                        'ناشئين': 'cadet',
                        'شباب': 'junior',
                        'كبار': 'senior'
                    }
                    age_group = age_group_mapping.get(age_group_raw.lower(), None)
                    if not age_group:
                        error_list.append(f"Row {index + 2}: Invalid age group '{age_group_raw}'")
                        continue
                    
                    # Determine age from age group (approximate)
                    age_from_group = {
                        'cadet': 15,
                        'junior': 25, 
                        'senior': 40
                    }
                    age = age_from_group.get(age_group, 20)
                    
                    # Check for duplicate players in same tournament
                    existing_player = Player.query.filter_by(
                        name=name,
                        club=club,
                        tournament_id=tournament_id
                    ).first()
                    
                    if existing_player:
                        error_list.append(f"Row {index + 2}: Player '{name}' from '{club}' already exists in this tournament")
                        continue
                    
                    # Create player object
                    player = Player(
                        name=name,
                        club=club,
                        coach=coach if coach and coach.lower() != 'nan' else None,
                        gender=Gender(gender),
                        age=age,
                        age_group=AgeGroup(age_group),
                        weight_category=None,  # Will be set based on weight if provided
                        tournament_id=tournament_id
                    )
                    
                    # For Kyourgi tournaments, try to determine weight category
                    if tournament.tournament_type == TournamentType.KYOURGI:
                        player.weight_category = WeightCategory.MIDDLE  # Default to middle
                    
                    db.session.add(player)
                    success_count += 1
                    
                except Exception as e:
                    error_list.append(f"Row {index + 2}: {str(e)}")
                    continue
            
            # Commit successful imports
            if success_count > 0:
                db.session.commit()
                flash(f'Successfully imported {success_count} players from Google Forms!', 'success')
                
                # Flash errors (if any)
                if error_list:
                    flash(f'{len(error_list)} rows had errors and were skipped:', 'warning')
                    for error in error_list[:5]:  # Show first 5 errors
                        flash(error, 'warning')
                    if len(error_list) > 5:
                        flash(f'... and {len(error_list) - 5} more errors', 'warning')
            else:
                db.session.rollback()
                flash('No players were imported due to errors.', 'error')
            
            return redirect(url_for('main.view_tournament', id=tournament_id))
            
        except Exception as e:
            flash(f'Error reading Excel file: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('google_forms_import.html', tournament=tournament, title='Import Google Forms Excel')

@main.route('/poomsae/score/<int:match_id>', methods=['GET', 'POST'])
@login_required
def poomsae_score(match_id):
    """Score Poomsae match using WT 5-judge system"""
    match = Match.query.get_or_404(match_id)
    
    # Check if tournament is Poomsae type
    if match.tournament.tournament_type != TournamentType.POOMSAE:
        flash('This route is only for Poomsae tournaments!', 'error')
        return redirect(url_for('main.view_tournament', id=match.tournament_id))
    
    # Check if user has permission to score
    if not current_user.can_score_matches():
        flash('You do not have permission to score matches!', 'error')
        return redirect(url_for('main.view_tournament', id=match.tournament_id))
    
    # Check if match already has scores
    existing_scores = MatchScore.query.filter_by(match_id=match_id).first()
    if existing_scores and existing_scores.judge_scores:
        flash('This match has already been scored!', 'warning')
        return redirect(url_for('main.view_tournament', id=match.tournament_id))
    
    if request.method == 'POST':
        try:
            # Create MatchScore record
            match_score = MatchScore(
                match_id=match_id,
                player_id=match.player1_id,  # In Poomsae, we typically score one player
                scored_by=current_user.id
            )
            db.session.add(match_score)
            db.session.flush()  # Get the ID without committing
            
            # Create 5 JudgeScore records
            for i in range(1, 6):
                accuracy_key = f'judge{i}_accuracy'
                presentation_key = f'judge{i}_presentation'
                
                accuracy = float(request.form.get(accuracy_key, 0.0))
                presentation = float(request.form.get(presentation_key, 0.0))
                
                judge_score = JudgeScore(
                    match_score_id=match_score.id,
                    judge_number=i,
                    accuracy=accuracy,
                    presentation=presentation
                )
                judge_score.calculate()  # Calculate total for this judge
                db.session.add(judge_score)
            
            # Calculate final score using WT system
            match_score.calculate_final_poomsae_score()
            
            # Mark match as completed
            match.completed = True
            
            db.session.commit()
            
            flash(f'Poomsae match scored successfully! Final score: {match_score.total_score}', 'success')
            return redirect(url_for('main.view_tournament', id=match.tournament_id))
            
        except ValueError as e:
            db.session.rollback()
            flash(f'Error calculating scores: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving scores: {str(e)}', 'error')
    
    # For GET request, render the scoring form
    return render_template('poomsae_score.html', match=match, title=f'Score Poomsae Match')