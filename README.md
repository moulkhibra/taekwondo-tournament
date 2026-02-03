# Taekwondo Tournament Management System

A comprehensive web application for managing Taekwondo tournaments with support for both Kyourgi (fighting) and Poomsae (forms) competitions.

## Features

- **Tournament Management**: Create and manage tournaments with full details
- **Player Registration**: Add players with automatic categorization
- **Excel Integration**: Import players from Excel files, export brackets to Excel
- **Qor3a Draw Algorithm**: Fair random bracket generation with BYE handling
- **Category Support**: Age groups (Cadet/Junior/Senior) and weight categories
- **Visual Brackets**: Interactive tournament bracket display
- **Export Options**: Download tournament data as TXT, PDF, or Excel
- **Responsive Design**: Works on desktop, tablet, and mobile

## System Requirements

- Python 3.8 or higher
- Modern web browser
- 2GB RAM minimum
- 100MB disk space

## Installation & Setup

### 1. Clone or Download the Project

```bash
# Navigate to your desired directory
cd /path/to/your/projects

# Extract the project files (if downloaded as ZIP)
# or clone if using git repository
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv taekwondo-env

# Activate virtual environment
# On Windows:
taekwondo-env\Scripts\activate
# On Linux/Mac:
source taekwondo-env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python run.py
```

The application will start at: `http://localhost:5000`

## Usage Guide

### Creating Your First Tournament

1. **Launch the Application**
   - Open your web browser
   - Navigate to `http://localhost:5000`

2. **Create Tournament**
   - Click "New Tournament" button
   - Fill in tournament details:
     - Tournament Name (e.g., "Summer Championship 2024")
     - Date and Location
     - Type: Kyourgi or Poomsae
   - Click "Create Tournament"

3. **Add Players**
   - Click "Add Player" button
   - Fill player information:
     - Full Name and Club
     - Gender and Age
     - Weight (required only for Kyourgi)
     - Select Tournament
   - Click "Add Player"
   - Repeat for all players

4. **Excel Integration (Optional)**
   - **Import Players from Excel:**
     - Click "Download Template" to get the Excel template
     - Fill the template with player data (Name, Club, Gender, Age, Weight)
     - Click "Import Excel" button on tournament page
     - Select the filled file and upload
   
   - **Export Brackets to Excel:**
     - Generate tournament draw first
     - Click "Export" dropdown and select "Export Brackets (Excel)"
     - Download the complete bracket structure with match details

5. **Generate Tournament Draw**
   - Click "Generate Draw" button
   - Select your tournament from dropdown
   - Click "Generate Draw"
   - The Qor3a algorithm will create fair brackets automatically

6. **View and Manage**
   - View tournament brackets by category
   - Export results as TXT, PDF, or Excel
   - Manage players (edit/delete as needed)

## Excel Integration

The system supports comprehensive Excel integration for both importing players and exporting tournament brackets.

### Excel Player Import

**Template Format:**
The Excel file must contain these exact columns:
- **Name** (required): Full name of the player
- **Club** (required): Club or organization name
- **Gender** (required): Male, Female, M, F (case-insensitive)
- **Age** (required): Age in years (14-80)
- **Weight** (required): Weight in kg (20-150)

**Steps to Import:**
1. Download template: Click "Download Template" from Excel Tools dropdown
2. Fill with player data following the format
3. Go to tournament page and click "Import Excel"
4. Select your filled file and upload
5. System validates and imports valid players, skipping duplicates

**Validation Rules:**
- Name and Club cannot be empty
- Age must be between 14-80 years
- Weight must be between 20-150 kg
- Gender values: Male/Female/M/F (variations accepted)
- No duplicate players in same tournament
- Invalid rows are skipped and reported

### Excel Bracket Export

**Exported Data Includes:**
- **Brackets Sheet**: All matches by category and round
  - Category name (e.g., "Male Junior Light Kyourgi")
  - Round number and match number
  - Player A and Player B names
  - Match status (BYE, Pending, Completed)
  - Club information for both players

- **Info Sheet**: Tournament summary
  - Tournament name, date, location
  - Total number of matches
  - Export timestamp

**Export Process:**
1. Generate tournament draw first
2. Click "Export" dropdown on tournament page
3. Select "Export Brackets (Excel)"
4. Download the generated Excel file

**File Format:**
- Format: Excel (.xlsx)
- Multiple sheets: Brackets + Info
- Auto-sized columns for readability
- Compatible with Excel 2007+ and LibreOffice

### Error Handling

**Import Errors:**
- **File validation**: Invalid format, empty file, missing columns
- **Data validation**: Invalid age/weight, missing required fields
- **Duplicate detection**: Same player from same club in tournament
- **Partial success**: Valid rows imported, errors reported separately

**Common Issues & Solutions:**
- **"Missing required columns"**: Ensure exact column names: Name, Club, Gender, Age, Weight
- **"Invalid gender value"**: Use Male, Female, M, or F only
- **"Age/weight out of range"**: Check values against requirements
- **"File too large"**: Split large imports into multiple files

## Qor3a Draw Algorithm

The system uses the "Qor3a" (قرعة - Arabic for draw/lottery) algorithm:

### How It Works

1. **Categorization**: Players grouped by (gender, age group, weight category/type)
2. **Random Shuffling**: Players randomly shuffled within each category
3. **BYE Handling**: Random player receives BYE for odd numbers
4. **Match Creation**: Sequential pairing creates first-round matches
5. **Bracket Generation**: Complete single-elimination tournament tree

### Age Groups

- **Cadet**: 14-17 years
- **Junior**: 18-34 years  
- **Senior**: 35+ years

### Weight Categories (Kyourgi Only)

- **Light**: Up to 68kg
- **Middle**: 68-80kg
- **Heavy**: Over 80kg

## Project Structure

```
taekwondo-tournament/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── models.py            # Database models (Tournament, Player, Match)
│   ├── routes.py            # Flask routes and API endpoints
│   ├── forms.py             # WTForms validation classes
│   ├── draw_algorithm.py    # Qor3a draw algorithm implementation
│   ├── excel_utils.py       # Excel import/export utilities
│   └── utils.py             # Helper functions
├── static/
│   ├── css/
│   │   └── style.css        # Custom CSS styling
│   └── js/
│       └── main.js          # JavaScript functionality
├── templates/
│   ├── base.html            # Base template with navbar
│   ├── dashboard.html       # Main dashboard view
│   ├── tournament_form.html # Tournament creation/editing
│   ├── tournament_view.html # Tournament details and brackets
│   ├── player_form.html     # Player creation/editing
│   ├── excel_import.html     # Excel player import interface
│   └── draw_form.html       # Draw generation interface
├── requirements.txt         # Python dependencies
├── run.py                  # Application entry point
└── README.md               # This documentation
```

## Database Schema

### Tables

1. **Tournament**: Tournament information and settings
2. **Player**: Player details and categorization
3. **Match**: Generated matches and bracket structure

### Relationships

- Tournament → Players (One-to-Many)
- Tournament → Matches (One-to-Many)
- Player → Matches (Many-to-Many as player1/player2)

## API Endpoints

- `GET /` - Dashboard with tournament list
- `GET/POST /tournament/new` - Create new tournament
- `GET /tournament/<id>` - View tournament details
- `GET/POST /player/new` - Add new player
- `GET/POST /player/<id>/edit` - Edit existing player
- `POST /player/<id>/delete` - Delete player
- `GET/POST /draw/generate` - Generate tournament draw
- `GET/POST /excel/import_players/<tournament_id>` - Import players from Excel
- `GET /excel/export_brackets/<tournament_id>` - Export brackets to Excel
- `GET /excel/download_template` - Download Excel template
- `GET /export/tournament/<id>/<format>` - Export tournament data (TXT/PDF)

## Security Features

- Input validation with WTForms
- SQL injection prevention with SQLAlchemy ORM
- XSS protection with Jinja2 autoescaping
- CSRF protection with Flask-WTF
- Server-side validation for all inputs

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill existing process on port 5000
   # On Linux/Mac:
   sudo lsof -ti:5000 | xargs kill -9
   # On Windows:
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

2. **Dependencies Installation Error**
   ```bash
   # Upgrade pip first
   pip install --upgrade pip
   # Then install requirements
   pip install -r requirements.txt
   ```

3. **Database Issues**
   ```bash
   # Delete existing database file
   rm tournament.db
   # Restart application to recreate
   python run.py
   ```

4. **Permission Issues**
   ```bash
   # Ensure proper permissions
   chmod +x run.py
   # Use virtual environment
   source taekwondo-env/bin/activate
   ```

### Getting Help

1. Check browser console for JavaScript errors
2. Review Flask logs in terminal
3. Verify all dependencies are installed
4. Ensure database file has write permissions

## Development Notes

### Adding New Features

1. Add database models in `app/models.py`
2. Create forms in `app/forms.py`
3. Implement routes in `app/routes.py`
4. Add templates in `templates/` directory
5. Update JavaScript/CSS as needed

### Database Migrations

For production use, consider implementing Flask-Migrate for database versioning:

```bash
pip install Flask-Migrate
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please refer to the project documentation or contact the development team.

---

**Enjoy managing your Taekwondo tournaments! 🥋**