# EVE Industry Tracker

A comprehensive web application for tracking and managing industrial jobs for EVE Online corporations. This application integrates with the EVE Online ESI API to provide real-time tracking of industrial activities, job requirements, and corporation management.

## Features

### 🚀 Core Functionality
- **EVE SSO Authentication** - Secure login using EVE Online credentials
- **Real-time Job Sync** - Automatic synchronization with EVE Online's ESI API
- **Multi-Character Support** - Multiple corporation members can contribute and track jobs
- **Admin Management** - Designated administrators can manage requirements and users

### 📊 Job Management
- **Required Jobs** - Create and track corporation industrial requirements
- **Priority System** - Set priorities (Critical, High, Medium, Low) for jobs
- **Deadline Tracking** - Set and monitor deadlines for completion
- **Progress Monitoring** - Track completion status and assignments
- **Activity Types** - Support for Manufacturing, Research, Copying, and Invention

### 👥 Corporation Features
- **Multi-User Access** - Multiple characters from the same corporation
- **Role-Based Permissions** - Admin and regular user roles
- **Corporation Integration** - Automatic corporation detection and verification

## Prerequisites

- Python 3.8 or higher
- EVE Online Developer Account
- ESI Application Registration

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd eve-industry-tracker
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# EVE SSO Configuration
EVE_CLIENT_ID=your-eve-client-id
EVE_CLIENT_SECRET=your-eve-client-secret
EVE_CALLBACK_URL=http://localhost:5000/sso/callback

# Database Configuration (optional, defaults to SQLite)
DATABASE_URL=sqlite:///eve_industry.db
```

### 5. Database Setup
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## EVE Online ESI Setup

### 1. Create EVE Developer Account
1. Go to [EVE Online Developers](https://developers.eveonline.com/)
2. Log in with your EVE Online account
3. Navigate to "Applications"

### 2. Create New Application
1. Click "Create New Application"
2. Fill in the application details:
   - **Name**: EVE Industry Tracker
   - **Description**: Corporation industrial job tracking and management
   - **Connection Type**: Authentication & API Access
   - **Permissions**: Select the following scopes:
     - `esi-industry.read_character_jobs.v1`
     - `esi-industry.read_corporation_jobs.v1`
     - `esi-characters.read_corporation_roles.v1`
   - **Callback URL**: `http://localhost:5000/sso/callback` (adjust for production)

### 3. Get Credentials
After creating the application, you'll receive:
- **Client ID**: Used in `EVE_CLIENT_ID`
- **Secret Key**: Used in `EVE_CLIENT_SECRET`

## Running the Application

### Development Mode
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Production Deployment
For production deployment, consider using:
- **WSGI Server**: Gunicorn, uWSGI
- **Web Server**: Nginx, Apache
- **Database**: PostgreSQL, MySQL (instead of SQLite)
- **Environment**: Docker, systemd

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Usage Guide

### First Time Setup

1. **Access the Application**
   - Navigate to `http://localhost:5000`
   - Click "Login with EVE Online"

2. **EVE SSO Authentication**
   - You'll be redirected to EVE Online's login page
   - Log in with your EVE credentials
   - Select the character you want to use
   - Authorize the requested permissions

3. **Admin Setup**
   - The first user from each corporation becomes an admin by default
   - Admins can promote other users to admin status

### Managing Required Jobs (Admins)

1. **Create Required Jobs**
   - Navigate to "Admin" → "Create Job"
   - Fill in the job details:
     - **Type ID**: EVE item type ID (use external tools for lookup)
     - **Item Name**: Name of the item to be produced
     - **Activity Type**: Manufacturing, Research, etc.
     - **Quantity**: How many items/runs needed
     - **Priority**: Critical, High, Medium, or Low
     - **Deadline**: Optional completion deadline
     - **Notes**: Additional instructions

2. **Manage Users**
   - Navigate to "Admin" → "Manage Users"
   - View all corporation members
   - Promote/demote admin status
   - Activate/deactivate users

### Tracking Jobs (All Users)

1. **View Required Jobs**
   - Navigate to "Required Jobs"
   - Filter by priority, activity type, or search by name
   - See deadlines and priority levels

2. **Monitor Industry Jobs**
   - Navigate to "Industry Jobs"
   - View real-time status of ongoing industrial activities
   - Sync with EVE Online using the "Sync Jobs" button

3. **Dashboard Overview**
   - Main dashboard shows summary statistics
   - Recent jobs and priority requirements
   - Quick access to common actions

## API Reference

### Internal API Endpoints

#### POST /api/sync-jobs
Synchronizes industry jobs with EVE Online ESI API.

**Response:**
```json
{
  "success": true
}
```

### EVE ESI Integration

The application uses the following ESI endpoints:

- **Character Industry Jobs**: `/characters/{character_id}/industry/jobs/`
- **Corporation Industry Jobs**: `/corporations/{corporation_id}/industry/jobs/`
- **Character Information**: `/characters/{character_id}/`
- **Corporation Information**: `/corporations/{corporation_id}/`
- **Universe Types**: `/universe/types/{type_id}/`

## Database Schema

### Users Table
- Character and corporation information
- Authentication tokens
- Admin status and permissions

### Required Jobs Table
- Corporation job requirements
- Priority and deadline information
- Creation and management metadata

### Industry Jobs Table
- Real EVE industry job data
- Status and timing information
- Facility and location details

### Job Assignments Table
- Links between required jobs and actual industry jobs
- Progress tracking

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Generated |
| `EVE_CLIENT_ID` | EVE SSO Client ID | Required |
| `EVE_CLIENT_SECRET` | EVE SSO Client Secret | Required |
| `EVE_CALLBACK_URL` | SSO callback URL | `http://localhost:5000/sso/callback` |
| `DATABASE_URL` | Database connection string | `sqlite:///eve_industry.db` |

### Application Settings

The application includes several configurable options:
- Automatic job sync interval (default: 5 minutes)
- Token refresh handling
- API timeout settings
- UI refresh rates

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify EVE SSO credentials are correct
   - Check callback URL matches ESI application settings
   - Ensure character has required permissions

2. **Job Sync Failures**
   - Check internet connectivity
   - Verify ESI API status
   - Confirm character tokens are valid

3. **Database Issues**
   - Ensure database file is writable
   - Check for disk space
   - Verify database schema is up to date

### Debug Mode
Enable debug mode in development:
```env
FLASK_ENV=development
```

### Logging
The application logs important events. Check console output for error details.

## Security Considerations

### Production Deployment
- Use HTTPS in production
- Set strong `SECRET_KEY`
- Secure database access
- Regular security updates
- Monitor access logs

### Token Management
- Access tokens expire after 20 minutes
- Refresh tokens are stored securely
- Tokens are automatically refreshed
- Users can revoke access at any time

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Use meaningful variable names
- Include comments for complex logic
- Test new features

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review EVE ESI documentation
- Contact the development team

## Acknowledgments

- CCP Games for the EVE Online API
- EVE Online development community
- Flask and Python communities
- Bootstrap for UI components

---

**Note**: This application is not affiliated with or endorsed by CCP Games. EVE Online and all related characters, names, marks, trademarks and logos are intellectual property of CCP hf.