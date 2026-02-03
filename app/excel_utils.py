import pandas as pd
import io
from datetime import datetime
from werkzeug.datastructures import FileStorage

from app.models import Player, Tournament, TournamentType, Gender, AgeGroup, WeightCategory
from app import db

class ExcelImportError(Exception):
    """Custom exception for Excel import errors"""
    pass

class ExcelImportExport:
    """
    Utility class for handling Excel import/export operations
    for Taekwondo Tournament Management System
    """
    
    @staticmethod
    def validate_excel_file(file: FileStorage) -> bool:
        """
        Validate uploaded Excel file
        
        Args:
            file: Uploaded FileStorage object
            
        Returns:
            bool: True if valid Excel file
            
        Raises:
            ExcelImportError: If file is invalid
        """
        if not file:
            raise ExcelImportError("No file provided")
        
        if not file.filename:
            raise ExcelImportError("No filename provided")
        
        # Check file extension
        allowed_extensions = ['.xlsx', '.xls']
        file_extension = file.filename.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise ExcelImportError("Invalid file format. Please upload an Excel file (.xlsx or .xls)")
        
        return True
    
    @staticmethod
    def read_excel_file(file: FileStorage) -> pd.DataFrame:
        """
        Read Excel file into pandas DataFrame
        
        Args:
            file: Uploaded FileStorage object
            
        Returns:
            pd.DataFrame: Excel data
            
        Raises:
            ExcelImportError: If file cannot be read
        """
        try:
            # Reset file pointer
            file.seek(0)
            
            # Read Excel file
            df = pd.read_excel(file, engine='openpyxl')
            
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            
            return df
            
        except Exception as e:
            raise ExcelImportError(f"Error reading Excel file: {str(e)}")
    
    @staticmethod
    def validate_excel_structure(df: pd.DataFrame) -> None:
        """
        Validate Excel file structure and required columns
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ExcelImportError: If structure is invalid
        """
        if df.empty:
            raise ExcelImportError("Excel file is empty")
        
        # Check required columns
        required_columns = ['Name', 'Club', 'Gender', 'Age', 'Weight']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ExcelImportError(
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Required columns: {', '.join(required_columns)}"
            )
    
    @staticmethod
    def clean_gender_value(gender_value) -> str:
        """
        Clean and standardize gender value
        
        Args:
            gender_value: Raw gender value from Excel
            
        Returns:
            str: Standardized gender value ('male' or 'female')
            
        Raises:
            ExcelImportError: If gender is invalid
        """
        if pd.isna(gender_value):
            raise ExcelImportError("Gender is required")
        
        gender_clean = str(gender_value).lower().strip()
        
        # Map various formats to standard values
        gender_mapping = {
            'male': 'male',
            'm': 'male',
            'man': 'male',
            'men': 'male',
            'boy': 'male',
            'female': 'female',
            'f': 'female',
            'woman': 'female',
            'women': 'female',
            'girl': 'female'
        }
        
        if gender_clean not in gender_mapping:
            raise ExcelImportError(f"Invalid gender value: '{gender_value}'. Valid values: Male, Female")
        
        return gender_mapping[gender_clean]
    
    @staticmethod
    def determine_age_group(age: int) -> AgeGroup:
        """
        Determine age group based on player age
        
        Args:
            age: Player age
            
        Returns:
            AgeGroup: Appropriate age group
            
        Raises:
            ExcelImportError: If age is out of valid range
        """
        if pd.isna(age):
            raise ExcelImportError("Age must be a valid number")
        
        age = int(age)
        
        if age < 14:
            raise ExcelImportError(f"Age {age} is too young. Minimum age is 14.")
        elif age > 80:
            raise ExcelImportError(f"Age {age} is too old. Maximum age is 80.")
        
        if age <= 17:
            return AgeGroup.CADET
        elif age <= 34:
            return AgeGroup.JUNIOR
        else:
            return AgeGroup.SENIOR
    
    @staticmethod
    def determine_weight_category(weight: float) -> WeightCategory:
        """
        Determine weight category based on player weight
        
        Args:
            weight: Player weight in kg
            
        Returns:
            WeightCategory: Appropriate weight category
            
        Raises:
            ExcelImportError: If weight is invalid
        """
        if pd.isna(weight):
            raise ExcelImportError("Weight must be a valid number")
        
        weight = float(weight)
        
        if weight < 20 or weight > 150:
            raise ExcelImportError(f"Weight {weight}kg is invalid. Valid range: 20-150kg.")
        
        if weight <= 68:
            return WeightCategory.LIGHT
        elif weight <= 80:
            return WeightCategory.MIDDLE
        else:
            return WeightCategory.HEAVY
    
    @staticmethod
    def validate_player_row(row_data, row_num: int) -> dict:
        """
        Validate and clean a single player row
        
        Args:
            row_data: Series containing player data
            row_num: Row number for error reporting
            
        Returns:
            Dict: Validated player data
            
        Raises:
            ExcelImportError: If validation fails
        """
        errors = []
        
        # Extract and validate each field
        try:
            name = str(row_data['Name']).strip()
            if not name or name.lower() == 'nan':
                errors.append("Name is required")
        except:
            errors.append("Name is required")
        
        try:
            club = str(row_data['Club']).strip()
            if not club or club.lower() == 'nan':
                errors.append("Club is required")
        except:
            errors.append("Club is required")
        
        # Gender
        try:
            gender = ExcelImportExport.clean_gender_value(row_data['Gender'])
        except Exception as e:
            errors.append(str(e))
        
        # Age
        try:
            age = int(row_data['Age'])
            age_group = ExcelImportExport.determine_age_group(age)
        except Exception as e:
            errors.append(str(e))
        
        # Weight
        try:
            weight = float(row_data['Weight'])
            weight_category = ExcelImportExport.determine_weight_category(weight)
        except Exception as e:
            errors.append(str(e))
        
        if errors:
            error_msg = f"Row {int(row_num) + 2}: " + "; ".join(errors)
            raise ExcelImportError(error_msg)
        
        return {
            'name': name,
            'club': club,
            'gender': gender,
            'age': age,
            'weight': weight,
            'age_group': age_group,
            'weight_category': weight_category
        }
    
    @staticmethod
    def import_players_from_excel(file: FileStorage, tournament_id: int) -> tuple:
        """
        Import players from Excel file
        
        Args:
            file: Uploaded Excel file
            tournament_id: ID of tournament to add players to
            
        Returns:
            Tuple[int, List[str]]: (success_count, list_of_errors)
            
        Raises:
            ExcelImportError: If file validation fails
        """
        # Validate file
        ExcelImportExport.validate_excel_file(file)
        
        # Read Excel file
        df = ExcelImportExport.read_excel_file(file)
        
        # Validate structure
        ExcelImportExport.validate_excel_structure(df)
        
        # Get tournament
        tournament = Tournament.query.get(tournament_id)
        if not tournament:
            raise ExcelImportError("Invalid tournament ID")
        
        success_count = 0
        error_list = []
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Validate row
                player_data = ExcelImportExport.validate_player_row(row, index)
                
                # Check for duplicate players in same tournament
                existing_player = db.session.query(Player).filter_by(
                    name=player_data['name'],
                    club=player_data['club'],
                    tournament_id=tournament_id
                ).first()
                
                if existing_player:
                    error_list.append(f"Row {int(index) + 2}: Player '{player_data['name']}' from '{player_data['club']}' already exists in this tournament")
                    continue
                
                # Create player object
                player = Player()
                player.name = player_data['name']
                player.club = player_data['club']
                player.gender = Gender(player_data['gender'])
                player.age = player_data['age']
                player.weight = player_data['weight']
                player.age_group = player_data['age_group']
                player.weight_category = player_data['weight_category']
                player.tournament_id = tournament_id
                
                # For Poomsae tournaments, weight category is not used
                if tournament.tournament_type == TournamentType.POOMSAE:
                    player.weight = None
                    player.weight_category = None
                
                db.session.add(player)
                success_count += 1
                
            except ExcelImportError as e:
                error_list.append(str(e))
                continue
            except Exception as e:
                error_list.append(f"Row {int(index) + 2}: Unexpected error - {str(e)}")
                continue
        
        # Commit successful imports
        if success_count > 0:
            db.session.commit()
        else:
            db.session.rollback()
        
        return success_count, error_list
    
    @staticmethod
    def export_brackets_to_excel(tournament_id: int) -> io.BytesIO:
        """
        Export tournament brackets to Excel
        
        Args:
            tournament_id: ID of tournament to export
            
        Returns:
            io.BytesIO: Excel file data
            
        Raises:
            ExcelImportError: If tournament not found
        """
        # Get tournament data
        tournament = Tournament.query.get(tournament_id)
        if not tournament:
            raise ExcelImportError("Tournament not found")
        
        # Get matches for this tournament
        from app.models import Match
        matches = Match.query.filter_by(tournament_id=tournament_id)\
                          .order_by(Match.round_number, Match.match_number)\
                          .all()
        
        # Prepare data for export
        export_data = []
        
        for match in matches:
            # Get player names
            player1_name = match.player1.name if match.player1 else "TBD"
            player2_name = match.player2.name if match.player2 else "TBD"
            
            # Determine status
            if match.is_bye:
                status = "BYE"
                player2_name = ""  # Clear player 2 for BYE matches
            elif match.completed:
                status = "Completed"
            else:
                status = "Pending"
            
            # Get category name
            category_parts = match.category_key.split('_')
            gender = 'Male' if category_parts[0] == 'male' else 'Female'
            age_group = category_parts[1].title()
            
            if tournament.tournament_type == TournamentType.KYOURGI:
                weight = category_parts[2].title()
                category_name = f"{gender} {age_group} {weight} Kyourgi"
            else:
                category_name = f"{gender} {age_group} Poomsae"
            
            export_data.append({
                'Category': category_name,
                'Round': match.round_number,
                'Match': match.match_number,
                'Player A': player1_name,
                'Player B': player2_name,
                'Status': status,
                'Club A': match.player1.club if match.player1 else "",
                'Club B': match.player2.club if match.player2 else ""
            })
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        # Use a more compatible approach
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main brackets sheet
            df.to_excel(writer, sheet_name='Brackets', index=False)
            
            # Auto-adjust column widths for brackets sheet
            worksheet = writer.sheets['Brackets']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Add tournament info sheet
            info_data = {
                'Field': ['Tournament Name', 'Date', 'Location', 'Type', 'Total Matches', 'Generated'],
                'Value': [
                    tournament.name,
                    tournament.date.strftime('%Y-%m-%d'),
                    tournament.location,
                    tournament.tournament_type.value.title(),
                    len(matches),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            info_df = pd.DataFrame(info_data)
            info_df.to_excel(writer, sheet_name='Info', index=False)
            
            # Auto-adjust info sheet columns
            info_worksheet = writer.sheets['Info']
            for column in info_worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                info_worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    
    @staticmethod
    def create_import_template() -> io.BytesIO:
        """
        Create Excel template for player import
        
        Returns:
            io.BytesIO: Excel template file data
        """
        # Create template data with examples
        template_data = [
            {
                'Name': 'John Doe',
                'Club': 'Taekwondo Academy',
                'Gender': 'Male',
                'Age': 25,
                'Weight': 75.5
            },
            {
                'Name': 'Jane Smith',
                'Club': 'Martial Arts Club',
                'Gender': 'Female',
                'Age': 19,
                'Weight': 62.0
            },
            {
                'Name': 'Ahmed Hassan',
                'Club': 'Sports Center',
                'Gender': 'Male',
                'Age': 16,
                'Weight': 65.0
            }
        ]
        
        df = pd.DataFrame(template_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write template sheet
            df.to_excel(writer, sheet_name='Players', index=False)
            
            # Add instructions sheet
            instructions_data = [
                ['Column', 'Required?', 'Description', 'Valid Values/Examples'],
                ['Name', 'Yes', 'Full name of player', 'John Doe, Jane Smith'],
                ['Club', 'Yes', 'Club or organization name', 'Taekwondo Academy'],
                ['Gender', 'Yes', 'Gender of player', 'Male, Female, M, F'],
                ['Age', 'Yes', 'Age in years (14-80)', '16, 25, 35'],
                ['Weight', 'Yes', 'Weight in kg (20-150)', '65.5, 75.0, 82.3']
            ]
            
            # Convert to DataFrame properly
            columns = instructions_data[0]
            rows = instructions_data[1:]
            instructions_df = pd.DataFrame(rows, columns=columns)
            instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
            
            # Auto-adjust column widths
            for sheet_name in ['Players', 'Instructions']:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output